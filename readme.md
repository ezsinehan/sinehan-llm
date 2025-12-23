## Goal

Backend-only service that:

1. ingests documents into a vector database (embeddings)
2. answers questions with retrieval-augmented generation (RAG) using an LLM
3. is easy to demo + talk about in interviews (clear architecture, endpoints, metrics)

## Minimal backend architecture

**Components**

* **API server** (REST): FastAPI (Python) or Node/Express.
* **Embedding model** (local): `bge-small-en` / `e5-small` via `sentence-transformers` (fast + easy).
* **Vector DB**: Qdrant (recommended) or Chroma (embedded).
* **LLM**: local via Ollama (simple) or OpenAI (if you want hosted).
* **Storage**: raw docs on disk + metadata in SQLite/Postgres (optional but good).

**Core flows**

* **Ingest**: upload → chunk → embed → upsert vectors (+ metadata).
* **Query**: question → embed → similarity search → build prompt with top-k chunks → LLM answer (+ citations).

## Deliverables

* Clean RAG backend with: ingestion pipeline, vector search, prompt assembly, streaming responses, citations, evaluation hooks.
* Dockerized stack (API + Qdrant).
* Basic auth/key + rate limit (optional but good).
* Observability: request ids, latency logs, token usage estimate, top-k retrieval debug output.

## API endpoints (backend only)

1. `POST /v1/collections`
   Create collection (dimension, distance metric).

2. `POST /v1/ingest`
   Body: `{collection, source_id, text | file, metadata}`
   Returns: `{doc_id, chunks_indexed, dimension}`

3. `POST /v1/query`
   Body: `{collection, question, top_k, filters, return_sources}`
   Returns: `{answer, sources:[{chunk, source_id, score, metadata}]}`

4. `GET /v1/health`
   Checks API + vectordb connectivity.

5. `DELETE /v1/source/{source_id}`
   Delete vectors for a source.

## Data model (simple, interview-friendly)

* **Chunk**: `{id, source_id, chunk_index, text, embedding_vector, metadata}`
* **Metadata** examples: `{"title":"...", "type":"pdf", "created_at":"...", "tags":["..."]}`

## Chunking strategy (keep it defensible)

* Split by headings/paragraphs first, then fallback to token/char window.
* Start with: `chunk_size ~ 800–1200 chars`, `overlap ~ 150–250 chars`.
* Store `chunk_index` to preserve ordering.

## Retrieval strategy (start simple, extendable)

* Similarity search top_k (e.g. 6–10).
* Optional: MMR (diversity) later.
* Optional: reranker later (cross-encoder).

## Prompt template (what the backend builds)

System:

* “Answer using ONLY the provided context. If missing, say you don’t know.”
  User:
* Question
* Context list: `[source_id:chunk_index] chunk text`

Return citations as `[source_id:chunk_index]`.

## Tech stack recommendation (backend-only, easiest to ship)

* **FastAPI + Qdrant + Ollama**
* Docker Compose: `api`, `qdrant`
* Local models:

  * embeddings: `sentence-transformers/all-MiniLM-L6-v2` (fast baseline)
  * LLM: any Ollama model (Llama/Qwen/Mistral)

## Repo structure (clean for interviews)

* `app/`

  * `main.py` (routes)
  * `config.py`
  * `ingest/` (chunking, loaders)
  * `retrieval/` (vectordb client, search)
  * `llm/` (provider interface: ollama/openai)
  * `rag/` (prompt builder, answer composer)
  * `schemas/` (pydantic models)
  * `utils/` (logging, ids)
* `docker-compose.yml`
* `README.md` (1-command run + curl examples)

## What to implement first (atomic order)

1. Qdrant running in Docker.
2. `/health` confirms API + Qdrant.
3. `/collections` create collection with correct vector dimension.
4. `/ingest` accepts raw text, chunks it, embeds it, upserts to Qdrant.
5. `/query` retrieves top_k chunks and returns them (no LLM yet).
6. Add LLM call (Ollama) and return final answer + citations.
7. Add delete-by-source + basic filters.

