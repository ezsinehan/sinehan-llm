# tests/test_chunk.py
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.chunk import Chunk, ChunkMetadata
from pydantic import ValidationError

print("Testing ChunkMetadata...")

# Test 1: Valid metadata creation
metadata = ChunkMetadata(
    doc_id="project1",
    chunk_index=5,
    section_title="Introduction",
    url="https://example.com",
    token_count=150,
    source_name="readme.md"
)
print("[OK] Valid metadata created")

# Test 2: chunk_id property
assert metadata.chunk_id == "project1_5", f"Expected 'project1_5', got '{metadata.chunk_id}'"
print("[OK] chunk_id property works correctly")

# Test 3: Optional url can be None
metadata_no_url = ChunkMetadata(
    doc_id="project2",
    chunk_index=0,
    section_title="Section",
    url=None,
    token_count=100,
    source_name="doc.md"
)
print("[OK] Optional url field accepts None")

# Test 4: Missing required field should fail
try:
    invalid = ChunkMetadata(
        doc_id="project3",
        # Missing chunk_index
        section_title="Test",
        token_count=50,
        source_name="test.md"
    )
    print("✗ Should have raised ValidationError for missing chunk_index")
except ValidationError as e:
    print("[OK] Missing required field correctly raises ValidationError")

# Test 5: Wrong type should fail
try:
    invalid = ChunkMetadata(
        doc_id="project4",
        chunk_index="not_an_int",  # Should be int
        section_title="Test",
        token_count=50,
        source_name="test.md"
    )
    print("✗ Should have raised ValidationError for wrong type")
except ValidationError as e:
    print("[OK] Wrong type correctly raises ValidationError")

print("\nTesting Chunk...")

# Test 6: Valid chunk creation
chunk = Chunk(
    text="# Introduction\nThis is the text...",
    metadata=metadata
)
print("[OK] Valid chunk created")

# Test 7: Missing metadata should fail
try:
    invalid_chunk = Chunk(
        text="Some text"
        # Missing metadata
    )
    print("✗ Should have raised ValidationError for missing metadata")
except ValidationError as e:
    print("[OK] Missing metadata correctly raises ValidationError")

print("\nAll tests passed! [OK]")