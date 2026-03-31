# FastAPI is the main class to create the app instance
# UploadFile  type for upload files
# File(...) dependencies to mark a parameter as a file upload
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

# Creates the app instance, app is used to register routes and configure the API
app = FastAPI()

# CORS: allow your UI (e.g. localhost:3000 or localhost:5173) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sinehan.dev", "https://www.sinehan.dev"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


# --- Step 7: Query (embed question → vector search top-k) ---

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    chunks: list[dict]  # each: text, doc_id, chunk_index, section_title, url, token_count, source_name, chunk_id, score


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Embed the question, search Qdrant for top-k similar chunks, return chunks with metadata and score."""
    from app.services.embedder import embed_text
    from app.services.vector_store import search

    try:
        query_vector = embed_text(request.question)
        chunks = search(query_vector=query_vector, top_k=request.top_k)
        return QueryResponse(chunks=chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Step 8 & 9: Answer (question + chunks → LLM) + citations ---

class AnswerRequest(BaseModel):
    question: str
    top_k: int = 5


def _chunk_to_citation(c: dict) -> dict:
    """Extract citation fields from a chunk dict (no full text)."""
    return {
        "chunk_id": c.get("chunk_id"),
        "doc_id": c.get("doc_id"),
        "section_title": c.get("section_title"),
        "url": c.get("url"),
        "source_name": c.get("source_name"),
    }


class AnswerResponse(BaseModel):
    answer: str
    citations: list[dict]  # each: chunk_id, doc_id, section_title, url, source_name


@app.post("/answer", response_model=AnswerResponse)
async def answer(request: AnswerRequest):
    """Run query (embed + search), then send question + chunks to Ollama; return answer and citations."""
    from app.services.embedder import embed_text
    from app.services.vector_store import search
    from app.services.llm import answer_from_chunks

    try:
        query_vector = embed_text(request.question)
        chunks = search(query_vector=query_vector, top_k=request.top_k)
        answer_text = answer_from_chunks(request.question, chunks)
        citations = [_chunk_to_citation(c) for c in chunks]
        return AnswerResponse(answer=answer_text, citations=citations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Step 3: Ingest (upload → extract → clean → chunk → embed → store) ---


def _doc_id_from_filename(filename: str) -> str:
    """Derive a safe doc_id from filename (e.g. 'My Doc.md' -> 'my-doc')."""
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    stem = stem.strip() or "doc"
    # Lowercase, replace non-alphanumeric with dash, collapse dashes
    safe = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return safe or "doc"


class IngestResponse(BaseModel):
    status: str
    doc_id: str
    source_name: str
    chunks_stored: int


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    doc_id: str | None = Form(None),
    url: str | None = Form(None),
):
    """
    Upload a markdown or text file: extract text, clean, chunk, embed, and store in Qdrant.
    Optional form fields: doc_id (default: from filename), url (optional link for citations).
    Re-ingesting the same doc_id replaces existing chunks for that doc.
    """
    from app.services.text_extractor import extract_text_from_markdown
    from app.services.text_cleaner import clean_text
    from app.services.chunker import chunk_markdown
    from app.services.embedder import embed_chunks
    from app.services.vector_store import (
        COLLECTION_NAME,
        ensure_collection,
        delete_by_doc_id,
        upsert_chunks,
    )

    try:
        raw = await extract_text_from_markdown(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cleaned = clean_text(raw)
    resolved_doc_id = doc_id if doc_id and doc_id.strip() else _doc_id_from_filename(file.filename or "doc.md")
    sourcename = file.filename or "document.md"

    chunks = chunk_markdown(cleaned, doc_id=resolved_doc_id, sourcename=sourcename, url=url or None)
    if not chunks:
        return IngestResponse(
            status="ok",
            doc_id=resolved_doc_id,
            source_name=sourcename,
            chunks_stored=0,
        )

    try:
        vectors = embed_chunks(chunks)
        ensure_collection(COLLECTION_NAME)
        delete_by_doc_id(resolved_doc_id, COLLECTION_NAME)
        upsert_chunks(chunks, vectors, COLLECTION_NAME)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return IngestResponse(
        status="ok",
        doc_id=resolved_doc_id,
        source_name=sourcename,
        chunks_stored=len(chunks),
    )
