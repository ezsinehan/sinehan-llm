import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from pydantic import BaseModel, field_validator

from app.rate_limit import limiter, ANSWER_LIMIT, INFO_LIMIT

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: allow your UI (e.g. Vite on :5173) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://sinehan.dev",
        "https://www.sinehan.dev",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# --- Answer (question + chunks → LLM) + citations ---

MAX_QUESTION_LENGTH = 500
MAX_TOP_K = 10


class AnswerRequest(BaseModel):
    question: str
    top_k: int = 5

    @field_validator("question")
    @classmethod
    def question_not_empty_or_too_long(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be empty")
        if len(v) > MAX_QUESTION_LENGTH:
            raise ValueError(f"question must be {MAX_QUESTION_LENGTH} characters or fewer")
        return v

    @field_validator("top_k")
    @classmethod
    def top_k_in_range(cls, v: int) -> int:
        if v < 1 or v > MAX_TOP_K:
            raise ValueError(f"top_k must be between 1 and {MAX_TOP_K}")
        return v


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


@app.get("/info")
@limiter.limit(INFO_LIMIT)
async def info(request: Request):
    """Return technical details about the RAG setup: stack info, document stats, service health."""
    from app.config import settings
    from app.services.vector_store import _get_client, COLLECTION_NAME

    # Stack info
    stack = {
        "llm_model": settings.ollama_model_name,
        "embedding_model": settings.embedding_model_name,
        "embedding_dimension": settings.embedding_dimension,
        "vector_db": "Qdrant",
    }

    # Document/chunk stats from Qdrant
    stats = {"total_chunks": 0, "documents": []}
    qdrant_ok = False
    try:
        client = _get_client()
        collection = client.get_collection(COLLECTION_NAME)
        stats["total_chunks"] = collection.points_count
        # Scroll all points to extract unique doc_ids
        all_points, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            with_payload=["doc_id", "source_name"],
            with_vectors=False,
        )
        doc_map = {}
        for p in all_points:
            doc_id = p.payload.get("doc_id", "unknown")
            if doc_id not in doc_map:
                doc_map[doc_id] = {"doc_id": doc_id, "source_name": p.payload.get("source_name", ""), "chunk_count": 0}
            doc_map[doc_id]["chunk_count"] += 1
        stats["documents"] = list(doc_map.values())
        qdrant_ok = True
    except Exception:
        pass

    # Ollama health check
    ollama_ok = False
    try:
        import httpx
        resp = httpx.get(f"{settings.ollama_url}/api/tags", timeout=3)
        ollama_ok = resp.status_code == 200
    except Exception:
        pass

    return {
        "stack": stack,
        "stats": stats,
        "health": {
            "qdrant": qdrant_ok,
            "ollama": ollama_ok,
        },
    }


@app.post("/answer", response_model=AnswerResponse)
@limiter.limit(ANSWER_LIMIT)
async def answer(request: Request, body: AnswerRequest):
    """Run query (embed + search), then send question + chunks to Ollama; return answer and citations."""
    from app.services.embedder import embed_text
    from app.services.vector_store import search
    from app.services.llm import answer_from_chunks

    try:
        query_vector = embed_text(body.question)
        chunks = search(query_vector=query_vector, top_k=body.top_k)
        answer_text = answer_from_chunks(body.question, chunks)
        citations = [_chunk_to_citation(c) for c in chunks]
        return AnswerResponse(answer=answer_text, citations=citations)
    except Exception as e:
        print(f"[/answer error] {e}")
        raise HTTPException(status_code=500, detail="System is currently unavailable. Please try again later.")


@app.post("/answer/stream")
@limiter.limit(ANSWER_LIMIT)
async def answer_stream(request: Request, body: AnswerRequest):
    """SSE streaming variant of /answer. Sends real phase events, streams tokens, then citations."""
    def event_stream():
        try:
            from app.services.embedder import embed_text
            from app.services.vector_store import search
            from app.services.llm import stream_answer_from_chunks

            yield f"data: {json.dumps({'phase': 'embedding'})}\n\n"
            query_vector = embed_text(body.question)

            yield f"data: {json.dumps({'phase': 'searching'})}\n\n"
            chunks = search(query_vector=query_vector, top_k=body.top_k)
            citations = [_chunk_to_citation(c) for c in chunks]

            yield f"data: {json.dumps({'phase': 'generating'})}\n\n"
            for token in stream_answer_from_chunks(body.question, chunks):
                yield f"data: {json.dumps({'token': token})}\n\n"

            yield f"data: {json.dumps({'citations': citations})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"[/answer/stream error] {e}")
            yield f"data: {json.dumps({'error': 'Stream interrupted'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/prompts")
@limiter.limit(INFO_LIMIT)
async def get_prompts(request: Request):
    """Return the current prompt configuration so the frontend can display it."""
    from app.services.llm import _load_prompts
    prompts = _load_prompts()
    return {
        "system": prompts.get("system", "").strip(),
        "user_template": prompts.get("user", "").strip(),
        "no_context": prompts.get("no_context", ""),
        "temperature": prompts.get("temperature", 0.2),
    }
