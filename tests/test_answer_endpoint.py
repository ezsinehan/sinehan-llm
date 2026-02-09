# tests/test_answer_endpoint.py
"""Automated tests for POST /answer (step 8/9). Mocks embedder, vector_store, and LLM."""
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_answer_returns_200_and_answer_citations():
    """POST /answer returns 200 with answer and citations array."""
    fake_vector = [0.0] * 384
    fake_chunks = [
        {
            "text": "The system ingests markdown.",
            "doc_id": "doc1",
            "chunk_index": 0,
            "section_title": "Overview",
            "url": "https://example.com",
            "token_count": 10,
            "source_name": "readme.md",
            "chunk_id": "doc1_0",
            "score": 0.9,
        }
    ]
    fake_answer = "This document describes a system for ingesting markdown."
    with patch("app.services.embedder.embed_text", return_value=fake_vector), patch(
        "app.services.vector_store.search", return_value=fake_chunks
    ), patch("app.services.llm.answer_from_chunks", return_value=fake_answer):
        response = client.post(
            "/answer",
            json={"question": "What is this about?", "top_k": 3},
        )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == fake_answer
    assert "citations" in data
    assert len(data["citations"]) == 1
    cit = data["citations"][0]
    assert cit["chunk_id"] == "doc1_0"
    assert cit["doc_id"] == "doc1"
    assert cit["section_title"] == "Overview"
    assert cit["url"] == "https://example.com"
    assert cit["source_name"] == "readme.md"
    assert "text" not in cit
    print("[PASS] POST /answer returns 200 with answer and citations (no text in citations)")


def test_answer_default_top_k():
    """POST /answer without top_k uses default 5; answer_from_chunks called with chunks."""
    fake_vector = [0.0] * 384
    fake_chunks = [{"text": "x", "doc_id": "d", "chunk_index": 0, "section_title": "S", "url": None, "token_count": 1, "source_name": "f.md", "chunk_id": "d_0", "score": 0.8}]
    with patch("app.services.embedder.embed_text", return_value=fake_vector), patch(
        "app.services.vector_store.search", return_value=fake_chunks
    ) as mock_search, patch("app.services.llm.answer_from_chunks", return_value="Yes.") as mock_llm:
        response = client.post("/answer", json={"question": "Hello?"})
    assert response.status_code == 200
    mock_search.assert_called_once()
    assert mock_search.call_args[1]["top_k"] == 5
    mock_llm.assert_called_once()
    assert mock_llm.call_args[0][0] == "Hello?"
    assert len(mock_llm.call_args[0][1]) == 1
    print("[PASS] POST /answer uses default top_k=5 and passes chunks to LLM")


def run_all():
    test_answer_returns_200_and_answer_citations()
    test_answer_default_top_k()
    print("\n" + "=" * 50)
    print("All answer endpoint tests passed.")
    print("=" * 50)


if __name__ == "__main__":
    run_all()
