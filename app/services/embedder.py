"""
Local embedding service using sentence-transformers.
Uses config.embedding_model_name; embeds chunk content as section_title + "\n\n" + text per step4 notes.
"""
from typing import List

from app.config import settings
from app.models.chunk import Chunk

# Model loaded on first use
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.embedding_model_name)
    return _model


def embed_text(text: str) -> List[float]:
    """Embed a single string; returns a list of floats (dimension = settings.embedding_dimension)."""
    model = _get_model()
    vec = model.encode(text, convert_to_numpy=True)
    return vec.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of strings; returns a list of vectors (each is a list of floats)."""
    if not texts:
        return []
    model = _get_model()
    matrix = model.encode(texts, convert_to_numpy=True)
    return [row.tolist() for row in matrix]


def text_to_embed_for_chunk(chunk: Chunk) -> str:
    """Build the string to embed for a chunk: section_title + newlines + text (per step4 / Option B)."""
    return f"{chunk.metadata.section_title}\n\n{chunk.text}"


def embed_chunks(chunks: List[Chunk]) -> List[List[float]]:
    """
    Embed a list of chunks. Each chunk is embedded as section_title + "\\n\\n" + chunk.text
    so the vector includes heading context. Returns one vector per chunk in the same order.
    """
    if not chunks:
        return []
    texts = [text_to_embed_for_chunk(c) for c in chunks]
    return embed_texts(texts)
