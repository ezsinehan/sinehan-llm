# Step 7: Query endpoint (embed question → vector search top-k)

## What we're doing

Step 6 stored chunks and their embeddings in Qdrant. Step 7 exposes a **query path**: the user sends a **question**; we **embed** it with the same model used for chunks, run **similarity search** in Qdrant (top-k by cosine similarity), and return the **retrieved chunks** (text + metadata + score) for use in the answer endpoint (step 8) and for citations.

So step 7 is: **question (string) → embed → vector search → list of chunks with metadata and score**.

---

## Inputs and outputs

- **Input:** User question (string), optional `top_k` (default 5).
- **Output:** List of chunk dicts, each with: `text`, `doc_id`, `chunk_index`, `section_title`, `url`, `token_count`, `source_name`, `chunk_id`, and `score` (similarity).

---

## Implementation

- **Embedding:** Reuse `embed_text(question)` from `app/services/embedder.py`. Same model and dimension (384) as ingestion.
- **Search:** `app/services/vector_store.search(query_vector, top_k, collection_name)`:
  - Uses Qdrant client `query_points(collection_name, query=query_vector, limit=top_k)` (qdrant-client 1.16+; `search()` was removed).
  - Returns `response.points`; each point has `payload` and `score`. We normalize to a list of dicts (payload + `score` as native float; `token_count` and `chunk_index` as int) for JSON.
- **API:** `POST /query` in `app/main.py`:
  - Request body: `{ "question": "...", "top_k": 5 }`.
  - Response: `{ "chunks": [ { "text", "doc_id", "chunk_index", "section_title", "url", "token_count", "source_name", "chunk_id", "score" }, ... ] }`.
  - Errors (embedder, Qdrant, serialization) return 500 with `detail` message.

---

## What we're not doing in step 7

- We're not calling the LLM or building the answer (step 8).
- We're not adding filtering by doc_id or other payload in the query (can be added later via `query_filter`).

---

## Summary

Step 7: **POST /query** accepts a question and optional top_k; embeds the question; runs vector similarity search in Qdrant (`query_points`); returns top-k chunks with text, metadata, and score for the answer step and citations.

---
[AI-GENERATED SUMMARY]

Step 7 Decisions - Query endpoint:
- Embed question with `embed_text(question)` (same model as ingestion).
- Vector search via `vector_store.search(query_vector, top_k)` using Qdrant `query_points(collection_name, query=query_vector, limit=top_k)`.
- Response: list of dicts with payload fields + `score` (native float for JSON).
- API: POST /query, body `{ question, top_k? }`, response `{ chunks }`; 500 with detail on error.

---

## Manual test

1. Start the API: `uvicorn app.main:app --reload` (from project root with venv).
2. Ensure Qdrant has data: run `python scripts/manual_test_chunking.py` once (without `--no-store`).
3. Run the manual query script: `python scripts/manual_test_query.py`  
   Or pass a question: `python scripts/manual_test_query.py "Your question" --top-k 5`  
   Or call the API directly (PowerShell):  
   `Invoke-RestMethod -Method Post -Uri http://localhost:8000/query -ContentType "application/json" -Body '{"question": "What is this about?", "top_k": 3}'`
