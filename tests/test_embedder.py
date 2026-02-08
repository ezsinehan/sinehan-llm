# tests/test_embedder.py
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.models.chunk import Chunk, ChunkMetadata
from app.services.embedder import text_to_embed_for_chunk, embed_texts, embed_chunks, embed_text


def test_text_to_embed_for_chunk():
    """Chunk text to embed must be section_title + newlines + text."""
    meta = ChunkMetadata(
        doc_id="d1",
        chunk_index=0,
        section_title="Getting Started",
        url=None,
        token_count=10,
        source_name="readme.md",
    )
    chunk = Chunk(text="Install with pip.", metadata=meta)
    out = text_to_embed_for_chunk(chunk)
    assert out == "Getting Started\n\nInstall with pip."
    print("[PASS] text_to_embed_for_chunk")


def test_embed_texts_empty():
    assert embed_texts([]) == []
    print("[PASS] embed_texts([]) returns []")


def test_embed_chunks_empty():
    assert embed_chunks([]) == []
    print("[PASS] embed_chunks([]) returns []")


def test_embed_text_shape():
    """Requires model and .env; returns list of floats of length embedding_dimension."""
    from app.config import settings
    vec = embed_text("Hello world.")
    assert isinstance(vec, list)
    assert len(vec) == settings.embedding_dimension
    assert all(isinstance(x, float) for x in vec)
    print(f"[PASS] embed_text returns list of {len(vec)} floats")


def test_embed_chunks_shape():
    """Requires model and .env; embed_chunks returns one vector per chunk."""
    meta = ChunkMetadata(
        doc_id="d1", chunk_index=0, section_title="Intro",
        url=None, token_count=5, source_name="x.md",
    )
    chunks = [Chunk(text="Short.", metadata=meta)]
    vectors = embed_chunks(chunks)
    from app.config import settings
    assert len(vectors) == 1
    assert len(vectors[0]) == settings.embedding_dimension
    print("[PASS] embed_chunks returns one vector per chunk")


if __name__ == "__main__":
    test_text_to_embed_for_chunk()
    test_embed_texts_empty()
    test_embed_chunks_empty()
    try:
        test_embed_text_shape()
        test_embed_chunks_shape()
    except Exception as e:
        print(f"[SKIP] Model tests (need .env + sentence-transformers): {e}")
    print("Done.")
