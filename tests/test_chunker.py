# tests/test_chunker.py
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.chunker import split_by_headings, chunk_markdown

print("Testing chunker (Step 1: Split by Headings)...\n")

# ============================================================================
# TESTS FOR split_by_headings()
# ============================================================================

# Test 1: Basic ## headings
def test_basic_headings():
    text = """## First Section
Content for first section.

## Second Section
Content for second section."""
    
    result = split_by_headings(text)
    
    assert len(result) == 2, f"Expected 2 sections, got {len(result)}"
    assert result[0][0] == "First Section", f"Expected title 'First Section', got '{result[0][0]}'"
    assert result[1][0] == "Second Section", f"Expected title 'Second Section', got '{result[1][0]}'"
    assert "Content for first section" in result[0][1], "First section content missing"
    assert "Content for second section" in result[1][1], "Second section content missing"
    print("[PASS] Basic ## headings split correctly")


# Test 2: Content before first heading (Introduction)
def test_intro_before_heading():
    text = """This is intro content before any heading.

## First Section
Content here."""
    
    result = split_by_headings(text)
    
    assert len(result) == 2, f"Expected 2 sections, got {len(result)}"
    assert result[0][0] == "Introduction", f"Expected 'Introduction', got '{result[0][0]}'"
    assert "intro content" in result[0][1], "Introduction content missing"
    assert result[1][0] == "First Section", f"Expected 'First Section', got '{result[1][0]}'"
    print("[PASS] Content before first heading becomes 'Introduction' section")


# Test 3: Empty section (heading with no content) should be dropped
def test_empty_section_dropped():
    text = """## Empty Section
## Section With Content
This section has content."""
    
    result = split_by_headings(text)
    
    assert len(result) == 1, f"Expected 1 section (empty dropped), got {len(result)}"
    assert result[0][0] == "Section With Content", f"Expected 'Section With Content', got '{result[0][0]}'"
    print("[PASS] Empty section (heading only) dropped correctly")


# Test 4: No ## headings at all
def test_no_headings():
    text = """This is just plain text.
No headings here at all.
Just paragraphs."""
    
    result = split_by_headings(text)
    
    assert len(result) == 1, f"Expected 1 section, got {len(result)}"
    assert result[0][0] == "Introduction", f"Expected 'Introduction', got '{result[0][0]}'"
    assert "plain text" in result[0][1], "Content missing"
    print("[PASS] Text without ## headings becomes single 'Introduction' section")


# Test 5: # headings should NOT be split points (only ##)
def test_single_hash_not_split():
    text = """# Project Title

This is intro under the project title.

## First Section
Content here."""
    
    result = split_by_headings(text)
    
    # # Project Title should be part of Introduction, not its own section
    assert len(result) == 2, f"Expected 2 sections, got {len(result)}"
    assert result[0][0] == "Introduction", f"Expected 'Introduction', got '{result[0][0]}'"
    assert "# Project Title" in result[0][1], "# heading should be in Introduction content"
    assert result[1][0] == "First Section", f"Expected 'First Section', got '{result[1][0]}'"
    print("[PASS] Single # headings are NOT split points (included in content)")


# Test 6: ### headings should NOT be split points (only ##)
def test_triple_hash_not_split():
    text = """## Main Section

### Subsection
Subsection content.

### Another Subsection
More content."""
    
    result = split_by_headings(text)
    
    # ### headings should stay within ## section
    assert len(result) == 1, f"Expected 1 section, got {len(result)}"
    assert result[0][0] == "Main Section", f"Expected 'Main Section', got '{result[0][0]}'"
    assert "### Subsection" in result[0][1], "### should be in section content"
    assert "### Another Subsection" in result[0][1], "### should be in section content"
    print("[PASS] Triple ### headings are NOT split points (included in content)")


# Test 7: Multiple empty sections in a row
def test_multiple_empty_sections():
    text = """## Empty One
## Empty Two
## Empty Three
## Has Content
Finally some content here."""
    
    result = split_by_headings(text)
    
    assert len(result) == 1, f"Expected 1 section, got {len(result)}"
    assert result[0][0] == "Has Content", f"Expected 'Has Content', got '{result[0][0]}'"
    print("[PASS] Multiple empty sections all dropped correctly")


# Test 8: Section with only whitespace after heading (should be dropped)
def test_whitespace_only_section():
    text = """## Whitespace Section
   
   
## Real Section
Actual content here."""
    
    result = split_by_headings(text)
    
    # Whitespace-only section should be dropped
    assert len(result) == 1, f"Expected 1 section, got {len(result)}"
    assert result[0][0] == "Real Section", f"Expected 'Real Section', got '{result[0][0]}'"
    print("[PASS] Whitespace-only section dropped correctly")


# Test 9: Empty text
def test_empty_text():
    text = ""
    
    result = split_by_headings(text)
    
    assert len(result) == 0, f"Expected 0 sections, got {len(result)}"
    print("[PASS] Empty text returns empty list")


# Test 10: Whitespace-only text
def test_whitespace_only_text():
    text = "   \n\n   \t   "
    
    result = split_by_headings(text)
    
    assert len(result) == 0, f"Expected 0 sections, got {len(result)}"
    print("[PASS] Whitespace-only text returns empty list")


# Test 11: Heading with extra spaces
def test_heading_extra_spaces():
    text = """##    Heading With Spaces   
Content here."""
    
    result = split_by_headings(text)
    
    assert len(result) == 1, f"Expected 1 section, got {len(result)}"
    # Title should be trimmed
    assert result[0][0] == "Heading With Spaces", f"Expected trimmed title, got '{result[0][0]}'"
    print("[PASS] Heading with extra spaces trimmed correctly")


# Test 12: Section title is plain text (no ## prefix)
def test_title_no_prefix():
    text = """## My Section Title
Content here."""
    
    result = split_by_headings(text)
    
    # Title should NOT include ##
    assert "##" not in result[0][0], f"Title should not include ##, got '{result[0][0]}'"
    assert result[0][0] == "My Section Title", f"Expected plain title, got '{result[0][0]}'"
    print("[PASS] Section title is plain text (no ## prefix)")


# ============================================================================
# TESTS FOR chunk_markdown() - Basic Step 1 functionality
# ============================================================================

# Test 13: chunk_markdown creates proper Chunk objects
def test_chunk_markdown_basic():
    text = """## First Section
Content for first.

## Second Section
Content for second."""
    
    chunks = chunk_markdown(text, doc_id="test-doc", sourcename="test.md", url="https://example.com")
    
    assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"
    
    # Check first chunk
    assert chunks[0].metadata.doc_id == "test-doc"
    assert chunks[0].metadata.chunk_index == 0
    assert chunks[0].metadata.section_title == "First Section"
    assert chunks[0].metadata.source_name == "test.md"
    assert chunks[0].metadata.url == "https://example.com"
    assert chunks[0].metadata.token_count > 0
    
    # Check second chunk
    assert chunks[1].metadata.chunk_index == 1
    assert chunks[1].metadata.section_title == "Second Section"
    
    print("[PASS] chunk_markdown creates proper Chunk objects with metadata")


# Test 14: chunk_id is derived correctly
def test_chunk_id_derived():
    text = """## Test Section
Some content."""
    
    chunks = chunk_markdown(text, doc_id="my-project", sourcename="file.md")
    
    expected_id = "my-project_0"
    assert chunks[0].metadata.chunk_id == expected_id, f"Expected '{expected_id}', got '{chunks[0].metadata.chunk_id}'"
    print("[PASS] chunk_id derived correctly as {doc_id}_{chunk_index}")


# Test 15: Token count is calculated
def test_token_count():
    text = """## Section
This is a test with some words."""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Token count should be positive and reasonable
    assert chunks[0].metadata.token_count > 0, "Token count should be positive"
    assert chunks[0].metadata.token_count < 100, "Token count should be reasonable for small text"
    print(f"[PASS] Token count calculated: {chunks[0].metadata.token_count} tokens")


# Test 16: URL is optional
def test_url_optional():
    text = """## Section
Content."""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    assert chunks[0].metadata.url is None, "URL should be None when not provided"
    print("[PASS] URL is optional (None when not provided)")


# Run all tests
def run_all_tests():
    # split_by_headings tests
    test_basic_headings()
    test_intro_before_heading()
    test_empty_section_dropped()
    test_no_headings()
    test_single_hash_not_split()
    test_triple_hash_not_split()
    test_multiple_empty_sections()
    test_whitespace_only_section()
    test_empty_text()
    test_whitespace_only_text()
    test_heading_extra_spaces()
    test_title_no_prefix()
    
    # chunk_markdown tests
    test_chunk_markdown_basic()
    test_chunk_id_derived()
    test_token_count()
    test_url_optional()
    
    print("\n" + "="*50)
    print("All Step 1 tests passed! [PASS]")
    print("="*50)


# Execute tests
if __name__ == "__main__":
    run_all_tests()

