# FastAPI is the main class to create the app instance
# UploadFile  type for upload files
# File(...) dependencies to mark a parameter as a file upload
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

# Creates the app instance, app is used to register routes and configure the API
app = FastAPI()


# --- Step 7: Query (embed question → vector search top-k) ---

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    chunks: list[dict]  # each: text, doc_id, chunk_index, section_title, url, token_count, source_name, chunk_id, score


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Embed the question, search Qdrant for top-k similar chunks, return chunks with metadata and score."""
    from fastapi import HTTPException
    from app.services.embedder import embed_text
    from app.services.vector_store import search

    try:
        query_vector = embed_text(request.question)
        chunks = search(query_vector=query_vector, top_k=request.top_k)
        return QueryResponse(chunks=chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Ingest (placeholder) ---

# @app.post is a decorator that registers a post endpoint!
# /ingest is the url path that becomes localhost:8000/ingest
# async is supported by FastAPI

# UploadFile provides: filename, content_type(MIME type), size, read(read content as bytes then decode for text)
@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    # Return response is a JSON response, fastAPI serializes the dict to JSON
    return {"status": "recieved", "filename": file.filename}
