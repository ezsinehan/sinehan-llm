# Step 6: Store in vector DB (Qdrant)

## What we're doing

After we have chunks (with metadata) and their embeddings (step 4 + 5), we need to put them somewhere that can do **similarity search**: given a question vector, return the most similar chunk vectors. That place is the vector DB. Step 6 is: **take the list of chunks and their vectors, and store them in Qdrant** so that later (step 7) we can search by embedding and get back chunk text + metadata for the LLM and for citations.

So step 6 is the bridge: **chunks + vectors in memory → chunks + vectors in Qdrant**.

---

## What you need to understand about Qdrant

**Why a vector DB at all?**  
A vector is just a list of numbers. To "find chunks similar to my question" we need to compare the question vector to every chunk vector (e.g. cosine similarity) and take the best matches. Doing that by hand over millions of vectors is slow. Qdrant (and similar DBs) store vectors in a structure optimized for this kind of search (approximate nearest neighbour, ANN), so we get fast "give me top-k by similarity" without writing the search ourselves.

**Three things Qdrant stores per record (it calls each record a "point"):**

1. **ID** – Unique identifier for the point. We need this so we can update or delete a specific chunk (e.g. when re-ingesting a document we delete all points for that doc_id, then add the new ones). We'll use **chunk_id** (e.g. `sinehan-rag_0`) as the point ID so it's stable and human-readable.

2. **Vector** – The embedding (list of floats, length = our embedding dimension, 384). This is what gets compared during search. Same dimension as our embedder output.

3. **Payload** – Extra data stored with the point. When we search, Qdrant returns the vector's payload with each hit. So we store **everything we need at query time**: the chunk text (so the LLM can read it) and the metadata (doc_id, section_title, url, etc.) so we can show citations and know where the chunk came from. Payload is a key-value map (JSON-serializable). No embedding in the payload—the vector is separate.

**Collection** – In Qdrant, points live in a **collection**. A collection has a name and a fixed **vector size** (and usually a distance metric, e.g. cosine). All points in that collection must have vectors of that size. We have one collection (e.g. `rag_chunks`) and all our chunk embeddings go there. When we create the collection we set the vector size to our embedding dimension (384) so it matches the embedder output.

**Summary:** One Qdrant **point** = one chunk. Point ID = chunk_id. Point vector = that chunk's embedding. Point payload = chunk text + metadata (doc_id, chunk_index, section_title, url, token_count, source_name). We put all points in one **collection** whose vector size is 384.

---

## Where the data comes from (inputs to step 6)

- **Chunks** – From the chunker: `List[Chunk]`. Each has `chunk.text` and `chunk.metadata` (doc_id, chunk_index, section_title, url, token_count, source_name, and derived chunk_id).
- **Vectors** – From the embedder: `embed_chunks(chunks)` returns `List[List[float]]`, one vector per chunk in the same order as chunks.
- **Config** – We already have `qdrant_url`, `qdrant_api_key` (step 2), and `embedding_dimension` (384). The client connects with url + api_key; the collection is created with size = embedding_dimension.

So step 6 does not chunk or embed; it **takes** chunks and vectors and **writes** them into Qdrant.

---

## Re-ingest: replacing all chunks for a document

We decided (step 4 notes) that doc_id is stable and that when we re-ingest a document we **replace** all chunks for that document. So when we upload "sinehan-rag" again:

1. **Delete** every point in the collection whose payload has `doc_id == "sinehan-rag"`. That clears the old chunks for that doc.
2. **Upsert** the new points (new chunks + new vectors) for that doc.

That way we don't end up with duplicate or stale chunks for the same doc. So step 6 needs two operations we can call: **delete all points for a given doc_id** (filter by payload), and **upsert a batch of points** (id, vector, payload per chunk).

---

## Exact shape of what we store (decisions)

- **Collection name** – Fixed name, e.g. `rag_chunks`. Could come from config later; for now a constant is fine.
- **Point ID** – `chunk.metadata.chunk_id` (e.g. `sinehan-rag_0`). String. Unique per chunk across the whole app.
- **Vector** – The corresponding element from `embed_chunks(chunks)`; length must equal collection's vector size (384).
- **Payload** – A dict we can build from each chunk, e.g.:
  - `text` → chunk.text
  - `doc_id`, `chunk_index`, `section_title`, `url`, `token_count`, `source_name` from chunk.metadata (chunk_id can be recomputed from doc_id + chunk_index so we don't have to store it in payload if we don't want, but storing it is fine too).

Payload must be JSON-serializable (strings, numbers, null, no custom objects). We'll use the same payload shape when we do search (step 7) so the API that returns "top-k chunks" gets back text and metadata without extra mapping.

---

## What we're not doing in step 6

- We're not building the ingestion HTTP endpoint here (that's step 3 territory); we're building the **store** that the ingestion pipeline will call. So a small module (e.g. a vector_store or qdrant service) with: ensure collection exists, delete by doc_id, upsert chunks+vectors. The actual "upload file → extract → clean → chunk → embed → store" wiring can live in the endpoint or in a separate orchestration function.
- We're not implementing search (step 7). Step 6 is only: write chunks + vectors into Qdrant and support "replace all chunks for this doc_id".

---

## Summary in one sentence

Step 6: **Create a Qdrant collection (if needed), and provide a way to delete all points for a doc_id and to upsert a batch of points (one per chunk: id=chunk_id, vector=embedding, payload=text+metadata) so that ingestion can persist chunks and their embeddings and later steps can search them.**

---
[AI-GENERATED SUMMARY]

Step 6 Decisions - Store in Qdrant:
- One Qdrant point per chunk: id = chunk_id (string), vector = embedding (list of 384 floats), payload = text + metadata (doc_id, chunk_index, section_title, url, token_count, source_name).
- Single collection (e.g. rag_chunks), vector size = config.embedding_dimension (384), distance = cosine.
- Client: QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key).
- Operations: (1) ensure_collection(collection_name) – create if not exists with correct vector size; (2) delete_by_doc_id(collection_name, doc_id) – delete points where payload["doc_id"] == doc_id; (3) upsert_chunks(collection_name, chunks, vectors) – build points from chunks + vectors, upsert to collection.
- Re-ingest: call delete_by_doc_id for the doc_id, then upsert_chunks with the new chunks and vectors.
- Dependency: qdrant-client. No embedding or chunking in this step; inputs are List[Chunk] and List[List[float]] from previous steps.
