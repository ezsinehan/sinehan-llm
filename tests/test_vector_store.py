# tests/test_vector_store.py
"""Automated tests for vector_store (step 6). Mocks Qdrant so no live DB needed."""
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.models.chunk import Chunk, ChunkMetadata
from app.services import vector_store

# Shorthands
_chunk_id_to_point_id = vector_store._chunk_id_to_point_id
_chunk_to_payload = vector_store._chunk_to_payload
COLLECTION_NAME = vector_store.COLLECTION_NAME


def test_chunk_id_to_point_id_deterministic():
    """Same chunk_id must produce the same UUID every time."""
    uid1 = _chunk_id_to_point_id("sample-doc_0")
    uid2 = _chunk_id_to_point_id("sample-doc_0")
    assert uid1 == uid2, "Same chunk_id must yield same UUID"
    assert isinstance(uid1, uuid.UUID)
    # Different chunk_id -> different UUID
    uid3 = _chunk_id_to_point_id("sample-doc_1")
    assert uid1 != uid3
    print("[PASS] _chunk_id_to_point_id is deterministic")


def test_chunk_to_payload_keys():
    """Payload must contain text + all metadata fields (JSON-serializable)."""
    meta = ChunkMetadata(
        doc_id="my-doc",
        chunk_index=2,
        section_title="Section Title",
        url="https://example.com",
        token_count=42,
        source_name="readme.md",
    )
    chunk = Chunk(text="Chunk content here.", metadata=meta)
    payload = _chunk_to_payload(chunk)
    assert payload["text"] == "Chunk content here."
    assert payload["doc_id"] == "my-doc"
    assert payload["chunk_index"] == 2
    assert payload["section_title"] == "Section Title"
    assert payload["url"] == "https://example.com"
    assert payload["token_count"] == 42
    assert payload["source_name"] == "readme.md"
    assert payload["chunk_id"] == "my-doc_2"
    print("[PASS] _chunk_to_payload has all required keys")


def test_chunk_to_payload_url_none():
    """Payload must allow url=None (optional)."""
    meta = ChunkMetadata(
        doc_id="d",
        chunk_index=0,
        section_title="Intro",
        url=None,
        token_count=5,
        source_name="x.md",
    )
    chunk = Chunk(text="Text", metadata=meta)
    payload = _chunk_to_payload(chunk)
    assert payload["url"] is None
    print("[PASS] _chunk_to_payload allows url=None")


def test_upsert_chunks_length_mismatch():
    """upsert_chunks must raise ValueError when chunks and vectors length differ."""
    meta = ChunkMetadata(
        doc_id="d", chunk_index=0, section_title="S", url=None, token_count=1, source_name="x.md"
    )
    chunks = [Chunk(text="One", metadata=meta)]
    vectors = [[0.1] * 384, [0.2] * 384]  # 2 vectors, 1 chunk
    with patch.object(vector_store, "_get_client", return_value=MagicMock()):
        try:
            vector_store.upsert_chunks(chunks, vectors, collection_name="test_coll")
        except ValueError as e:
            assert "same length" in str(e)
            print("[PASS] upsert_chunks raises on length mismatch")
            return
    assert False, "Expected ValueError"


def test_ensure_collection_creates_when_not_exists():
    """When collection does not exist, create_collection and create_payload_index are called."""
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False
    with patch.object(vector_store, "_get_client", return_value=mock_client):
        vector_store.ensure_collection(collection_name="test_coll")
    mock_client.create_collection.assert_called_once()
    call_kw = mock_client.create_collection.call_args[1]
    assert call_kw["collection_name"] == "test_coll"
    assert call_kw["vectors_config"].size == 384
    mock_client.create_payload_index.assert_called_once()
    idx_call = mock_client.create_payload_index.call_args[1]
    assert idx_call["collection_name"] == "test_coll"
    assert idx_call["field_name"] == "doc_id"
    assert idx_call["field_schema"] == "keyword"
    print("[PASS] ensure_collection creates collection and index when not exists")


def test_ensure_collection_skips_create_when_exists():
    """When collection exists, create_collection is not called; create_payload_index still called."""
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    with patch.object(vector_store, "_get_client", return_value=mock_client):
        vector_store.ensure_collection(collection_name="test_coll")
    mock_client.create_collection.assert_not_called()
    mock_client.create_payload_index.assert_called_once()
    print("[PASS] ensure_collection skips create when collection exists")


def test_delete_by_doc_id_calls_delete_with_filter():
    """delete_by_doc_id must call client.delete with Filter on doc_id."""
    mock_client = MagicMock()
    with patch.object(vector_store, "_get_client", return_value=mock_client):
        vector_store.delete_by_doc_id("my-doc-id", collection_name="test_coll")
    mock_client.delete.assert_called_once()
    call_kw = mock_client.delete.call_args[1]
    assert call_kw["collection_name"] == "test_coll"
    selector = call_kw["points_selector"]
    assert selector.filter.must[0].key == "doc_id"
    assert selector.filter.must[0].match.value == "my-doc-id"
    print("[PASS] delete_by_doc_id calls delete with doc_id filter")


def test_upsert_chunks_builds_points():
    """upsert_chunks builds PointStructs with UUID id, vector, and full payload."""
    meta = ChunkMetadata(
        doc_id="doc1",
        chunk_index=0,
        section_title="Title",
        url=None,
        token_count=10,
        source_name="f.md",
    )
    chunks = [Chunk(text="Hello.", metadata=meta)]
    vectors = [[0.5] * 384]
    mock_client = MagicMock()
    with patch.object(vector_store, "_get_client", return_value=mock_client):
        vector_store.upsert_chunks(chunks, vectors, collection_name="test_coll")
    mock_client.upsert.assert_called_once()
    call_kw = mock_client.upsert.call_args[1]
    assert call_kw["collection_name"] == "test_coll"
    points = call_kw["points"]
    assert len(points) == 1
    pt = points[0]
    assert isinstance(pt.id, uuid.UUID)
    assert pt.id == _chunk_id_to_point_id("doc1_0")
    assert pt.vector == [0.5] * 384
    assert pt.payload["text"] == "Hello."
    assert pt.payload["doc_id"] == "doc1"
    assert pt.payload["chunk_id"] == "doc1_0"
    print("[PASS] upsert_chunks builds correct PointStructs")


def run_all():
    test_chunk_id_to_point_id_deterministic()
    test_chunk_to_payload_keys()
    test_chunk_to_payload_url_none()
    test_upsert_chunks_length_mismatch()
    test_ensure_collection_creates_when_not_exists()
    test_ensure_collection_skips_create_when_exists()
    test_delete_by_doc_id_calls_delete_with_filter()
    test_upsert_chunks_builds_points()
    print("\n" + "=" * 50)
    print("All vector_store tests passed.")
    print("=" * 50)


if __name__ == "__main__":
    run_all()
