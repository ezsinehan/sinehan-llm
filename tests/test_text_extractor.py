# tests/test_text_extractor.py
import sys
from pathlib import Path
import asyncio

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.text_extractor import extract_text_from_markdown

# Mock UploadFile class that mimics FastAPI's UploadFile interface
class MockUploadFile:
    """Simple mock of FastAPI's UploadFile for testing"""
    def __init__(self, content: bytes, filename: str = "test.md"):
        self.content = content
        self.filename = filename
    
    async def read(self) -> bytes:
        """Async read method that returns the content bytes"""
        # Simulate async I/O by yielding control briefly
        await asyncio.sleep(0.001)
        return self.content

print("Testing extract_text_from_markdown...\n")

# Test 1: Valid UTF-8 markdown extraction
async def test_valid_markdown():
    markdown_content = "# Hello World\n\nThis is a **test** markdown file."
    mock_file = MockUploadFile(
        content=markdown_content.encode("utf-8"),
        filename="test.md"
    )
    
    result = await extract_text_from_markdown(mock_file)
    assert result == markdown_content, f"Expected markdown content, got: {result[:50]}..."
    print("✓ Valid UTF-8 markdown extracted successfully")

# Test 2: Empty file
async def test_empty_file():
    mock_file = MockUploadFile(
        content=b"",
        filename="empty.md"
    )
    
    result = await extract_text_from_markdown(mock_file)
    assert result == "", "Empty file should return empty string"
    print("✓ Empty file handled correctly")

# Test 3: Markdown with special characters
async def test_special_characters():
    markdown_content = "# Test\n\nUnicode: 🚀 émojis & symbols: ©®™"
    mock_file = MockUploadFile(
        content=markdown_content.encode("utf-8"),
        filename="special.md"
    )
    
    result = await extract_text_from_markdown(mock_file)
    assert result == markdown_content, "Special characters should be preserved"
    print("✓ Special characters and unicode handled correctly")

# Test 4: Invalid UTF-8 encoding (should raise ValueError)
async def test_invalid_utf8():
    # Create bytes that are not valid UTF-8 (e.g., invalid byte sequence)
    invalid_bytes = b'\xff\xfe\x00\x01'  # Invalid UTF-8 sequence
    mock_file = MockUploadFile(
        content=invalid_bytes,
        filename="invalid.bin"
    )
    
    try:
        result = await extract_text_from_markdown(mock_file)
        print("✗ Should have raised ValueError for invalid UTF-8")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "invalid.bin" in str(e), "Error message should include filename"
        print("✓ Invalid UTF-8 correctly raises ValueError with filename")

# Test 5: Multi-line markdown
async def test_multiline_markdown():
    markdown_content = """# Title

## Section 1

This is paragraph one.

## Section 2

This is paragraph two with **bold** and *italic* text.
"""
    mock_file = MockUploadFile(
        content=markdown_content.encode("utf-8"),
        filename="multiline.md"
    )
    
    result = await extract_text_from_markdown(mock_file)
    assert result == markdown_content, "Multi-line markdown should be preserved"
    assert "\n" in result, "Should contain newlines"
    print("✓ Multi-line markdown extracted correctly")

# Run all tests
async def run_all_tests():
    await test_valid_markdown()
    await test_empty_file()
    await test_special_characters()
    await test_invalid_utf8()
    await test_multiline_markdown()
    print("\nAll tests passed! ✓")

# Execute tests
if __name__ == "__main__":
    asyncio.run(run_all_tests())