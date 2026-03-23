# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sinehan RAG is a Retrieval-Augmented Generation system that ingests markdown documentation, chunks it, embeds it locally, stores vectors in Qdrant, and answers user questions via Google Gemini.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload

# Run all tests
python tests/run_all_tests.py

# Run a single test file
python tests/test_chunker.py

# Manual pipeline scripts
python scripts/manual_test_chunking.py [file.md]  # ingest markdown
python scripts/manual_test_query.py               # test vector search
python scripts/manual_test_answer.py              # test LLM answer
python scripts/delete_all_qdrant.py               # clear vector DB
```

## Architecture

**Request pipeline (ingest):**
`UploadFile → text_extractor → text_cleaner → chunker → embedder → vector_store`

**Request pipeline (answer):**
`question → embedder → vector_store (similarity search) → llm (Gemini) → answer + citations`

**Key services in `app/services/`:**

- `chunker.py` — 4-step markdown chunking: (1) split by `##` headings, (2) split large sections by paragraphs (>600 tokens), (3) split by sentences/list items, (4) merge chunks <100 tokens with neighbors in same section. Content before the first `##` becomes "Introduction".
- `embedder.py` — Local embeddings via `sentence-transformers` (`BAAI/bge-small-en-v1.5`, 384-dim). Embeds as `"{section_title}\n\n{chunk_text}"`.
- `vector_store.py` — Qdrant Cloud client; stores/retrieves chunks with metadata.
- `llm.py` — Gemini integration; uses low temperature (0.2), enforces third-person answers about Sinehan, refuses off-topic questions.
- `text_cleaner.py` — Normalizes whitespace/newlines before chunking.
- `text_extractor.py` — Reads UTF-8 text from FastAPI `UploadFile`.

**API endpoints (`app/main.py`):**
- `POST /ingest` — Upload a markdown/text file; optional `doc_id`, `url` params.
- `POST /query` — Semantic search; returns top-k chunks with scores.
- `POST /answer` — Full RAG: returns `{ answer, citations }`.

**Configuration (`app/config.py`):** Pydantic Settings reads from `.env`:
- `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`
- `QDRANT_URL`, `QDRANT_API_KEY`
- `EMBEDDING_MODEL_NAME`, `EMBEDDING_DIMENSION`

**Chunk metadata:** `doc_id`, `chunk_index`, `section_title`, `url`, `token_count`, `source_name`. `chunk_id = "{doc_id}_{chunk_index}"`. Token counting uses `tiktoken` with `cl100k_base`.

## Testing

Tests use plain Python scripts with assertions (no pytest). `tests/run_all_tests.py` runs all test files sequentially. `test_chunker.py` is the largest file (~3900 lines) covering all four chunking steps extensively.

## Deployment

Python 3.11.9 (see `runtime.txt`). Procfile: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. See `docs/deploy.md` for Railway/Render environment variable setup.
