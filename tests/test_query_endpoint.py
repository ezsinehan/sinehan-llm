# tests/test_query_endpoint.py
"""Automated tests for POST /query (step 7). Mocks embedder and vector_store."""
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_query_returns_200_and_chunks_shape():
    """POST /query with question returns 200 and chunks array with text, score, metadata."""
    fake_vector = [0.0] * 384
    fake_chunks = [
        {
            "text": "Fake chunk text.",
            "doc_id": "doc1",
            "chunk_index": 0,
            "section_title": "Section",
            "url": None,
            "token_count": 10,
            "source_name": "x.md",
            "chunk_id": "doc1_0",
            "score": 0.9,
        }
    ]
    with patch("app.services.embedder.embed_text", return_value=fake_vector), patch(
        "app.services.vector_store.search", return_value=fake_chunks
    ):
        response = client.post(
            "/query",
            json={"question": "What is this about?", "top_k": 3},
        )
    assert response.status_code == 200
    data = response.json()
    assert "chunks" in data
    assert len(data["chunks"]) == 1
    c = data["chunks"][0]
    assert c["text"] == "Fake chunk text."
    assert c["score"] == 0.9
    assert c["doc_id"] == "doc1"
    assert c["chunk_id"] == "doc1_0"
    print("[PASS] POST /query returns 200 and chunks with text, score, metadata")


def test_query_default_top_k():
    """POST /query without top_k uses default; embed_text and search called once."""
    fake_vector = [0.0] * 384
    with patch("app.services.embedder.embed_text", return_value=fake_vector) as mock_embed, patch(
        "app.services.vector_store.search", return_value=[]
    ) as mock_search:
        response = client.post("/query", json={"question": "Hello"})
    assert response.status_code == 200
    mock_embed.assert_called_once_with("Hello")
    mock_search.assert_called_once()
    call_kw = mock_search.call_args[1]
    assert call_kw["top_k"] == 5
    print("[PASS] POST /query uses default top_k=5")


def run_all():
    test_query_returns_200_and_chunks_shape()
    test_query_default_top_k()
    print("\n" + "=" * 50)
    print("All query endpoint tests passed.")
    print("=" * 50)


if __name__ == "__main__":
    run_all()
