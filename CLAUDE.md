# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sinehan RAG is a Retrieval-Augmented Generation system that ingests markdown documentation, chunks it, embeds it locally, stores vectors in a local Qdrant instance (Docker), and answers user questions via a local Ollama LLM.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive CLI (main way to use the system)
python cli.py

# Run dev server (FastAPI — needed for website integration)
uvicorn app.main:app --reload

# Run all tests
python tests/run_all_tests.py

# Run a single test file
python tests/test_chunker.py

# Manual pipeline scripts (low-level debugging)
python scripts/manual_test_chunking.py [file.md]  # ingest markdown
python scripts/manual_test_query.py               # test vector search
python scripts/manual_test_answer.py              # test LLM answer
python scripts/delete_all_qdrant.py               # clear vector DB
```

## CLI (cli.py)

Run `python cli.py` to enter the interactive session. Slash commands:
- `/ingest <file>` — ingest a markdown file (optionally `--doc-id <id> --url <url>`)
- `/docs` — list all ingested documents
- `/clear <doc_id>` — remove a document from Qdrant
- `/help` — show help
- `/exit` — quit

Anything else typed is sent to the RAG pipeline as a question. Calls services directly — FastAPI server does not need to be running.

## Architecture

**Request pipeline (ingest):**
`UploadFile → text_extractor → text_cleaner → chunker → embedder → vector_store`

**Request pipeline (answer):**
`question → embedder → vector_store (similarity search) → llm (Ollama) → answer + citations`

**Key services in `app/services/`:**

- `chunker.py` — 4-step markdown chunking: (1) split by `##` headings, (2) split large sections by paragraphs (>600 tokens), (3) split by sentences/list items, (4) merge chunks <100 tokens with neighbors in same section. Content before the first `##` becomes "Introduction".
- `embedder.py` — Local embeddings via `sentence-transformers` (`BAAI/bge-small-en-v1.5`, 384-dim). Embeds as `"{section_title}\n\n{chunk_text}"`.
- `vector_store.py` — Qdrant client (local Docker); stores/retrieves chunks with metadata. `qdrant_api_key` is optional (empty = no auth, used for local instances).
- `llm.py` — Ollama integration via OpenAI-compatible API. Prompting is externalized to `prompts.yaml` (project root). LLM roleplays as Sinehan (first person).
- `text_cleaner.py` — Normalizes whitespace/newlines before chunking.
- `text_extractor.py` — Reads UTF-8 text from FastAPI `UploadFile`.

**API endpoints (`app/main.py`):**
- `GET /info` — Returns stack info, document stats, and service health (Qdrant/Ollama).
- `POST /answer` — Full RAG: returns `{ answer, citations }`. Input validated (question max 500 chars, top_k 1–10).
- `POST /answer/stream` — SSE streaming with real phase events: `{"phase": "embedding"}` → `{"phase": "searching"}` → `{"phase": "generating"}` → `{"token": "..."}` per token → `{"citations": [...]}` → `[DONE]`. Frontend falls back to `/answer` if this returns non-200.
- `GET /prompts` — Returns current prompt config (`system`, `user_template`, `no_context`, `temperature`) from `prompts.yaml`.

Ingest and query endpoints are not exposed on the API — use the CLI for ingestion.

**Prompt configuration (`prompts.yaml`):** All LLM prompting lives here — `system` (persona), `user` (template with `{context}`/`{question}` placeholders), `no_context` (fallback), `temperature`. Editable without code changes.

**Configuration (`app/config.py`):** Pydantic Settings reads from `.env`:
- `OLLAMA_URL` (default: `http://localhost:11434`), `OLLAMA_MODEL_NAME` (currently `llama3.2:3b` in `.env`), `OLLAMA_MAX_TOKENS`
- `QDRANT_URL`, `QDRANT_API_KEY` (optional, leave empty for local Docker)
- `EMBEDDING_MODEL_NAME`, `EMBEDDING_DIMENSION`

**Chunk metadata:** `doc_id`, `chunk_index`, `section_title`, `url`, `token_count`, `source_name`. `chunk_id = "{doc_id}_{chunk_index}"`. Token counting uses `tiktoken` with `cl100k_base`.

## Infrastructure

- **Qdrant** runs in Docker: `docker run -d --name qdrant -p 6333:6333 -v <project>/qdrant_storage:/qdrant/storage qdrant/qdrant`
- **Ollama** runs as a local service (install from ollama.com). Pull a model: `ollama pull llama3.2:3b`
- **Embeddings** are fully local via sentence-transformers (no external API needed)

## Testing

Tests use plain Python scripts with assertions (no pytest). `tests/run_all_tests.py` runs all test files sequentially. `test_chunker.py` is the largest file (~3900 lines) covering all four chunking steps extensively.

## Deployment

Python 3.11.9 (see `runtime.txt`). Target: self-hosted VPS with Qdrant + Ollama running as services, FastAPI served via uvicorn behind a reverse proxy.

### Cloudflare Tunnel (dev)

Exposes the local FastAPI server to `api.sinehan.dev` via a named tunnel.

- **Config:** `.cloudflared/config.yml` — routes `api.sinehan.dev` → `http://localhost:8000`, catch-all → 404
- **Tunnel ID:** `0de7fad1-b29c-471e-997a-e6b7da4e57c5`
- **Credentials:** stored in `~/.cloudflared/` (not in repo)

```powershell
# Start everything (Qdrant + uvicorn + tunnel) in one command
.\run_tunnel.ps1

# Route DNS (one-time)
cloudflared tunnel route dns api api.sinehan.dev
```

`run_tunnel.ps1` activates the venv, starts the Qdrant Docker container (if not running), launches uvicorn, and starts the Cloudflare tunnel. Ctrl+C stops all processes.

Domain is on name.com with Cloudflare DNS protection.

### Security

- Rate limiting via `slowapi` (configured in `app/rate_limit.py`)
- Input validation on `/answer` (question length, top_k range)
- Error messages are sanitized — no internal details exposed to clients
- CORS restricted to `localhost:5173` and `sinehan.dev`
