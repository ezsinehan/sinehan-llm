# Sinehan RAG

Sinehan RAG is a retrieval-augmented generation (RAG) project. It ingests markdown documentation, chunks it with structure-aware rules, embeds chunks locally, stores them in a vector database (Qdrant), and answers user questions by retrieving the most relevant chunks and sending them with the question to a local LLM (Ollama). You control the docs, so chunking is deterministic and optimized for your headings and paragraph structure. The stack is: **FastAPI** (API server), **sentence-transformers** with **BAAI/bge-small-en-v1.5** (local embeddings, 384 dimensions), **local Qdrant** (Docker, vector store), and **Ollama** (local LLM for answers). There is no LangChain; the RAG flow (chunk, embed, search, prompt, generate) is explicit.

---

## Getting Started

Install dependencies with pip. Create a virtual environment and activate it before installing. Then run the API server and upload your first markdown document.

- **Create a venv:** `python -m venv venv`
- **Activate (Windows):** `.\venv\Scripts\activate`
- **Install:** `pip install -r requirements.txt`
- **Run the server:** `uvicorn app.main:app --reload` (default: http://localhost:8000)
- **Ingest a doc:** Use the `/ingest` endpoint (see API Overview) or run `python scripts/manual_test_chunking.py` to process `sinehan_rag.md` and store chunks in Qdrant.

You can pass an optional URL when ingesting so that citations in answers link back to the source. The system accepts only markdown (or UTF-8 text) for ingestion; PDF is not supported. The default document name used by the manual chunking script is `sinehan_rag.md` with doc_id `sinehan-rag`.

---

## Configuration

All configuration is via environment variables (e.g. a `.env` file in the project root). Pydantic Settings loads them.

**LLM (Ollama):**
- **OLLAMA_URL** (optional, default `http://localhost:11434`): URL where Ollama is running.
- **OLLAMA_MODEL_NAME** (optional, default `qwen2.5:7b`): Model used for generating answers. Pull it first with `ollama pull <model>`.
- **OLLAMA_MAX_TOKENS** (optional, default `8192`): Max tokens for LLM responses.

**Vector DB (local Qdrant via Docker):**
- **QDRANT_URL** (required): Your Qdrant instance URL (e.g. `http://localhost:6333`).
- **QDRANT_API_KEY** (optional): Leave empty for local Docker instances.

**Embedding model:**
- **EMBEDDING_MODEL_NAME** (required): Model name for sentence-transformers; default is `BAAI/bge-small-en-v1.5`.
- **EMBEDDING_DIMENSION** (optional, default `384`): Vector size; must match the model (384 for bge-small-en-v1.5). Used when creating the Qdrant collection.

The chunker uses fixed thresholds you can rely on when writing docs: **MAX_TOKENS (600)** and **MIN_TOKENS (100)**. Section titles are stored in chunk metadata for citations; the heading line is not duplicated in chunk text. When embedding, the system uses `section_title + "\n\n" + chunk.text` so the vector has full context. Only markdown (or UTF-8 text) is accepted; the pipeline uses regex-based parsing and does not include heavy NLP dependencies.

---

## API Overview

The API has three main HTTP endpoints. All are POST. The server runs with FastAPI and CORS is configured for `sinehan.dev`.

### POST /ingest

Upload a markdown or UTF-8 text file to be processed and stored in Qdrant.

- **Content-Type:** multipart form.
- **Body (form):**
  - **file** (required): The markdown or text file.
  - **doc_id** (optional): Stable, human-readable identifier for this document (e.g. `sinehan-rag`). If omitted, it is derived from the filename (e.g. `My Doc.md` → `my-doc`). Re-ingesting with the same doc_id replaces all existing chunks for that document.
  - **url** (optional): Link to attach to chunks for citations (e.g. `https://example.com/sinehan-rag`).
- **Response (JSON):** `{ "status": "ok", "doc_id": "...", "source_name": "...", "chunks_stored": N }`. On error: 400 for invalid/non-UTF-8 file, 500 with `detail` for embedding or Qdrant errors.

Pipeline: extract text (UTF-8) → clean (normalize newlines/whitespace) → chunk (structure-aware) → embed (local model) → ensure Qdrant collection exists → delete existing points for doc_id → upsert new points. The vector store collection name is `rag_chunks`.

### POST /query

Retrieve the top-k chunks most similar to a question (no LLM call).

- **Content-Type:** application/json.
- **Body (JSON):** `{ "question": "Your question here.", "top_k": 5 }`. `top_k` is optional (default 5).
- **Response (JSON):** `{ "chunks": [ { "text", "doc_id", "chunk_index", "section_title", "url", "token_count", "source_name", "chunk_id", "score" }, ... ] }`. Each chunk has the full text and metadata; `score` is the similarity score. `url` may be null.

The server embeds the question with the same model used for ingestion, then runs a vector similarity search in Qdrant and returns the chunks in order of relevance.

### POST /answer

Ask a question and get an LLM-generated answer plus citations (the main RAG endpoint).

- **Content-Type:** application/json.
- **Body (JSON):** `{ "question": "Your question here.", "top_k": 5 }`. `top_k` is optional (default 5).
- **Response (JSON):** `{ "answer": "The model's answer text...", "citations": [ { "chunk_id", "doc_id", "section_title", "url", "source_name" }, ... ] }`. Citations are in the same order as the retrieved chunks; each citation does not include the full chunk text, only metadata for display and linking. `url` may be null.

Flow: embed question → search Qdrant for top-k chunks → build a prompt with question and chunk texts (numbered by section) → call Ollama → return the answer and the list of citations. The LLM is instructed to answer only from the provided context and to say so if the answer is not in the context.

---

## Chunking Pipeline

The pipeline runs in four steps. Understanding them helps you write docs that chunk well.

**Step 1: Split by headings.** The chunker splits only on level-two headings (`##`). The top-level `#` is treated as project or doc title and stays in the first section. Content before the first `##` becomes a section titled "Introduction". Subheadings like `###` are left inside the section and are not split points. Empty sections (a heading with no content) are dropped. Section titles are stored as plain text in metadata (no `##` prefix).

**Step 2: Split by paragraphs.** If a section is larger than MAX_TOKENS (600), it is split by paragraphs. Paragraphs are separated by two or more newlines. Each resulting chunk keeps the same section_title. The `##` heading line is removed from the chunk text; citations use metadata (section_title and url). If a section has only one paragraph and it is over the limit, the pipeline continues to Step 3 for that paragraph.

**Step 3: Split by sentences and list items.** If a paragraph is still over MAX_TOKENS, it is split into units: sentences (split on `. `, `! `, `? `) and list items (lines starting with `-`, `*`, or `1.`). List items are never split in the middle. Units are then grouped in order until the next unit would exceed the token limit. A single very long sentence with no period stays as one chunk. The chunker uses simple sentence boundaries; avoid abbreviations like "U.S." or "e.g." in the middle of sentences if they could trigger a false split.

**Step 4: Merge small chunks.** Chunks smaller than MIN_TOKENS (100) are merged with a sibling in the same section. Merging is backward (into the previous chunk) when possible; if the first chunk is small, it is merged forward into the next. Merging only happens within the same section, so section boundaries are preserved.

After all steps, each chunk has: doc_id, chunk_index, section_title, url (optional), token_count, and source_name. chunk_id is derived as `{doc_id}_{chunk_index}`. Token counting uses tiktoken with cl100k_base. Embeddings are computed over the combined section_title and chunk text so that retrieval and citations stay aligned.

---

## Reference: Thresholds and Edge Cases

- **MAX_TOKENS:** 600. Sections at or below this size stay as one chunk; larger sections are split by paragraphs, then by sentences/list items if needed. The limit is soft (e.g. a 620-token paragraph can be kept whole).
- **MIN_TOKENS:** 100. Chunks below this are merged with an adjacent chunk in the same section (backward or forward). No cross-section merging.
- **Empty sections:** A `##` heading with no content or only whitespace is dropped.
- **No `##` headings:** The whole document is one section titled "Introduction".
- **Re-ingest:** Use the same doc_id so the system can delete all existing points for that doc and upsert the new chunks; chunk_index is reassigned 0, 1, 2, ...
- **List items:** Lines starting with `-`, `*`, or `1. ` are one indivisible unit; never split mid-item.
- **Tokenizer:** tiktoken, cl100k_base.

---

## Scripts and Manual Tests

From the project root with the venv activated:

- **manual_test_chunking.py:** Runs the full pipeline (clean → chunk → embed → store) on a markdown file. Default file is `sinehan_rag.md`; default doc_id is `sinehan-rag`. Usage: `python scripts/manual_test_chunking.py` or `python scripts/manual_test_chunking.py path/to/file.md`. Flags: `--no-embed` (chunk only), `--no-store` (embed but do not write to Qdrant).
- **manual_test_query.py:** Calls POST /query and prints the retrieved chunks. Requires the server and Qdrant to have data. Usage: `python scripts/manual_test_query.py` or with a question and `--top-k N`.
- **manual_test_answer.py:** Calls POST /answer and prints the answer and citations. Requires the server, Qdrant data, and Ollama running. Usage: `python scripts/manual_test_answer.py` or with a question and `--top-k N`.

---

## Writing Docs for Good Chunking

Use clear `##` headings for each major section. Keep paragraphs under roughly 600 tokens when you can. Use lists where they fit; each list item is one unit and is never split in the middle. Avoid one long block with no paragraph or sentence boundaries. Small sections are fine; chunks under 100 tokens are merged with a sibling in the same section, preserving section identity in metadata.

---

## Summary for the LLM

Sinehan RAG is a RAG API: FastAPI + local embeddings (bge-small-en-v1.5, 384d) + local Qdrant (Docker) + Ollama (local LLM). Ingest markdown via POST /ingest (multipart: file, optional doc_id and url). Ask questions via POST /answer (JSON: question, optional top_k); response is answer text plus citations (chunk_id, doc_id, section_title, url, source_name). POST /query returns top-k chunks without calling the LLM. Chunking is structure-aware: split on `##`, then by paragraph, then by sentence/list; merge chunks under 100 tokens within the same section. Config: OLLAMA_URL, OLLAMA_MODEL_NAME, QDRANT_URL, QDRANT_API_KEY (optional), EMBEDDING_MODEL_NAME, EMBEDDING_DIMENSION. Default doc is sinehan_rag.md with doc_id sinehan-rag.
