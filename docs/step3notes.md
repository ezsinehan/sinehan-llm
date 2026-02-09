Now we are onto step three building the ingestion endpoint...

For this we need to create a FastAPI endpoint that accepts document uploads, which includes FastAPI application with an ingestion endpoint, an HTTP endpoint accepting pdfs, text, etc returning a success response. 

For this we need a couple dependencies, fastapi(the web framework), uvicorn(ASGI server to run FastAPI), python-multipart(required for file uploads in FastAPI)

Starting with a blank ingestion http endpoint which will simply take the document in and return success

Lets test this first go into to the venv (./venv/Scripts/Activate.ps1(for windows)) then run uvicorn app.main:app --reload, then go to http://127.0.0.1:8000/docs for the interactive API docs that FastAPI generates, you can test the endpoint on the gui and it works there.

Nice step 3 is complete now the endpoint accepts documents next I need to process the uploaded documents...

---

## Implementation: full pipeline (later)

The ingestion endpoint now runs the full pipeline:

1. **Accept upload:** `POST /ingest` with multipart form: required `file` (markdown or UTF-8 text), optional `doc_id`, optional `url`.
2. **Extract:** Read file as UTF-8 (via `extract_text_from_markdown`). Non-UTF-8 returns 400.
3. **Clean:** `clean_text(raw)` — normalize newlines, whitespace.
4. **Chunk:** `chunk_markdown(cleaned, doc_id=..., sourcename=filename, url=...)`. Metadata includes doc_id, section_title, source_name, url.
5. **Embed:** `embed_chunks(chunks)` — same model as query (section_title + text per chunk).
6. **Store:** `ensure_collection` → `delete_by_doc_id(doc_id)` (re-ingest replaces) → `upsert_chunks(chunks, vectors)`.

**doc_id:** If not provided, derived from filename (e.g. `My Doc.md` → `my-doc`). Safe for re-ingest: same doc_id replaces previous chunks.

**Response:** `{ "status": "ok", "doc_id": "...", "source_name": "...", "chunks_stored": N }`. Errors (embedding, Qdrant) return 500 with detail.

**Supported files:** Markdown and any UTF-8 text file. PDF not yet supported (would require a separate extractor).

**How to test:** Use FastAPI docs at `http://localhost:8000/docs` (try the `/ingest` endpoint with a .md file). Or PowerShell: `Invoke-RestMethod -Method Post -Uri http://localhost:8000/ingest -Form @{ file = Get-Item -Path .\sample_doc.md }`. Optional form fields: `doc_id`, `url`.