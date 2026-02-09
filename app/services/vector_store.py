"""
Step 6: Store chunks and their embeddings in Qdrant.
Provides: ensure_collection, delete_by_doc_id, upsert_chunks.
"""

import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import settings
from app.models.chunk import Chunk

# Single collection for all RAG chunks (step6notes).
COLLECTION_NAME = "rag_chunks"

# Namespace for deterministic UUIDs from chunk_id (Qdrant point IDs must be UUID or int).
_NAMESPACE_CHUNK_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "sinehanllm.rag.chunk_id")


def _chunk_id_to_point_id(chunk_id: str) -> uuid.UUID:
    """Map chunk_id (e.g. sample-doc_0) to a deterministic UUID for Qdrant point ID."""
    return uuid.uuid5(_NAMESPACE_CHUNK_ID, chunk_id)


def _get_client() -> QdrantClient:
    """Return a Qdrant client using settings (url + api_key)."""
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )


def ensure_collection(collection_name: str = COLLECTION_NAME) -> None:
    """
    Create the collection if it does not exist.
    Vector size = settings.embedding_dimension (384), distance = cosine.
    Ensures a payload index on doc_id (keyword) so delete_by_doc_id filter works.
    """
    client = _get_client()
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimension,
                distance=Distance.COSINE,
            ),
        )
    # Index on doc_id required for filtering/deleting by doc_id (Qdrant Cloud).
    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="doc_id",
            field_schema="keyword",
        )
    except Exception as e:
        if "already exists" in str(e).lower():
            pass
        else:
            raise


def delete_by_doc_id(
    doc_id: str,
    collection_name: str = COLLECTION_NAME,
) -> None:
    """
    Delete all points in the collection whose payload has doc_id == doc_id.
    Used when re-ingesting a document to replace its chunks.
    """
    client = _get_client()
    client.delete(
        collection_name=collection_name,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id),
                    ),
                ],
            ),
        ),
    )


def _chunk_to_payload(chunk: Chunk) -> dict:
    """Build JSON-serializable payload from chunk (text + metadata)."""
    m = chunk.metadata
    return {
        "text": chunk.text,
        "doc_id": m.doc_id,
        "chunk_index": m.chunk_index,
        "section_title": m.section_title,
        "url": m.url,
        "token_count": m.token_count,
        "source_name": m.source_name,
        "chunk_id": m.chunk_id,
    }


def search(
    query_vector: List[float],
    top_k: int = 5,
    collection_name: str = COLLECTION_NAME,
) -> List[dict]:
    """
    Similarity search: return top-k points closest to query_vector.
    Each result is a dict with payload (text, doc_id, chunk_index, section_title, url,
    token_count, source_name, chunk_id) plus "score" (similarity).
    """
    client = _get_client()
    # qdrant-client 1.16+ uses query_points (search was removed)
    response = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
    )
    hits = response.points
    out = []
    for h in hits:
        payload = dict(h.payload) if h.payload else {}
        # Ensure score and any numeric payload fields are native types for JSON.
        payload["score"] = float(h.score)
        if "token_count" in payload:
            payload["token_count"] = int(payload["token_count"])
        if "chunk_index" in payload:
            payload["chunk_index"] = int(payload["chunk_index"])
        out.append(payload)
    return out


def upsert_chunks(
    chunks: List[Chunk],
    vectors: List[List[float]],
    collection_name: str = COLLECTION_NAME,
) -> None:
    """
    Upsert one point per chunk: id=UUID(chunk_id), vector=embedding, payload=text+metadata.
    Qdrant accepts only UUID or int point IDs; we use a deterministic UUID from chunk_id.
    chunks and vectors must be in the same order and same length.
    """
    if len(chunks) != len(vectors):
        raise ValueError("chunks and vectors must have the same length")
    client = _get_client()
    points = [
        PointStruct(
            id=_chunk_id_to_point_id(chunk.metadata.chunk_id),
            vector=vec,
            payload=_chunk_to_payload(chunk),
        )
        for chunk, vec in zip(chunks, vectors)
    ]
    client.upsert(collection_name=collection_name, points=points)
