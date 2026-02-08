# tests/test_chunker.py
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.chunker import (
    split_by_headings, 
    chunk_markdown,
    remove_heading_line,
    split_by_paragraphs,
    split_into_units,
    split_into_sentences,
    group_units_by_tokens,
    merge_small_chunks,
    count_tokens,
    MAX_TOKENS,
    MIN_TOKENS
)

print("Testing chunker...\n")
print("=" * 50)
print("STEP 1: Split by Headings")
print("=" * 50)

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
# TESTS FOR chunk_markdown() - Basic functionality
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


# Test 13b: Heading line is removed from chunk text (Option B)
def test_heading_removed_from_content():
    text = """## My Section
This is the content."""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Chunk text should NOT contain the ## heading line
    assert "##" not in chunks[0].text, f"Heading should be removed, got: {chunks[0].text}"
    assert "My Section" not in chunks[0].text, f"Heading text should be removed, got: {chunks[0].text}"
    assert "This is the content" in chunks[0].text, "Content should be preserved"
    # But section_title metadata should have it
    assert chunks[0].metadata.section_title == "My Section"
    print("[PASS] Heading line removed from chunk text (metadata only)")


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


# ============================================================================
# STEP 2: Helper Functions
# ============================================================================

print("\n" + "=" * 50)
print("STEP 2: Paragraph Splitting Helpers")
print("=" * 50)


# Test 17: remove_heading_line basic
def test_remove_heading_line_basic():
    content = """## My Heading
This is the content after the heading."""
    
    result = remove_heading_line(content)
    
    assert "##" not in result, f"## should be removed, got: {result}"
    assert "My Heading" not in result, f"Heading text should be removed, got: {result}"
    assert "This is the content" in result, "Content should be preserved"
    print("[PASS] remove_heading_line removes ## heading line")


# Test 18: remove_heading_line preserves content
def test_remove_heading_line_preserves_content():
    content = """## Heading
First paragraph.

Second paragraph.

### Subheading
More content."""
    
    result = remove_heading_line(content)
    
    assert "First paragraph" in result
    assert "Second paragraph" in result
    assert "### Subheading" in result, "### should be preserved (only ## removed)"
    assert "More content" in result
    print("[PASS] remove_heading_line preserves all content except ## line")


# Test 19: remove_heading_line with no heading
def test_remove_heading_line_no_heading():
    content = "Just some content without a heading."
    
    result = remove_heading_line(content)
    
    assert result == content.strip(), "Content without heading should be unchanged"
    print("[PASS] remove_heading_line handles content without heading")


# Test 20: split_by_paragraphs basic
def test_split_by_paragraphs_basic():
    text = """First paragraph here.

Second paragraph here.

Third paragraph here."""
    
    result = split_by_paragraphs(text)
    
    assert len(result) == 3, f"Expected 3 paragraphs, got {len(result)}"
    assert "First paragraph" in result[0]
    assert "Second paragraph" in result[1]
    assert "Third paragraph" in result[2]
    print("[PASS] split_by_paragraphs splits on double newlines")


# Test 21: split_by_paragraphs handles multiple newlines
def test_split_by_paragraphs_multiple_newlines():
    text = """First paragraph.



Second paragraph."""
    
    result = split_by_paragraphs(text)
    
    assert len(result) == 2, f"Expected 2 paragraphs, got {len(result)}"
    print("[PASS] split_by_paragraphs handles 3+ newlines as single split")


# Test 22: split_by_paragraphs filters empty
def test_split_by_paragraphs_filters_empty():
    text = """

First paragraph.

   

Second paragraph.

"""
    
    result = split_by_paragraphs(text)
    
    assert len(result) == 2, f"Expected 2 paragraphs (empty filtered), got {len(result)}"
    print("[PASS] split_by_paragraphs filters empty paragraphs")


# Test 23: count_tokens works
def test_count_tokens():
    text = "Hello world"
    
    result = count_tokens(text)
    
    assert result > 0, "Should have positive token count"
    assert result < 10, "Simple text should have few tokens"
    print(f"[PASS] count_tokens works ({result} tokens for 'Hello world')")


# ============================================================================
# STEP 2: Paragraph Splitting Logic
# ============================================================================

print("\n" + "=" * 50)
print("STEP 2: Paragraph Splitting When > 600 Tokens")
print("=" * 50)


# Test 24: Small section stays as single chunk
def test_small_section_single_chunk():
    text = """## Small Section
This is a small section with just a few words.

It has two paragraphs but both are tiny."""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    assert len(chunks) == 1, f"Small section should stay as 1 chunk, got {len(chunks)}"
    assert chunks[0].metadata.token_count <= MAX_TOKENS
    print(f"[PASS] Small section ({chunks[0].metadata.token_count} tokens) stays as single chunk")


# Test 25: Large section splits into paragraph chunks
def test_large_section_splits_by_paragraph():
    # Create a section with multiple paragraphs that together exceed 600 tokens
    # "Word " is ~1 token in tiktoken, so 150 "Word " = ~150 tokens per paragraph
    # 5 paragraphs x 150 tokens = ~750 tokens total (> 600 threshold)
    para1 = "First paragraph. " + "Word " * 150
    para2 = "Second paragraph. " + "Word " * 150  
    para3 = "Third paragraph. " + "Word " * 150
    para4 = "Fourth paragraph. " + "Word " * 150
    para5 = "Fifth paragraph. " + "Word " * 150
    
    text = f"""## Large Section
{para1}

{para2}

{para3}

{para4}

{para5}"""
    
    # Verify total is actually > 600 tokens
    from app.services.chunker import count_tokens, remove_heading_line
    content = remove_heading_line(text[text.find('\n')+1:])  # Remove heading
    total_tokens = count_tokens(content)
    assert total_tokens > MAX_TOKENS, f"Test setup error: section only has {total_tokens} tokens"
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Should have 5 chunks (one per paragraph)
    assert len(chunks) == 5, f"Expected 5 chunks (one per paragraph), got {len(chunks)}"
    print(f"[PASS] Large section ({total_tokens} tokens) split into {len(chunks)} paragraph chunks")


# Test 26: All paragraph chunks have same section_title
def test_paragraph_chunks_same_section_title():
    # Use larger paragraphs to ensure section exceeds 600 tokens
    para1 = "First paragraph content. " + "Word " * 250
    para2 = "Second paragraph content. " + "Word " * 250
    para3 = "Third paragraph content. " + "Word " * 250
    
    text = f"""## My Important Section
{para1}

{para2}

{para3}"""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Should have multiple chunks
    assert len(chunks) >= 3, f"Expected at least 3 chunks, got {len(chunks)}"
    
    # All chunks should have the same section_title
    for i, chunk in enumerate(chunks):
        assert chunk.metadata.section_title == "My Important Section", \
            f"Chunk {i} should have section_title 'My Important Section', got '{chunk.metadata.section_title}'"
    print("[PASS] All paragraph chunks inherit same section_title")


# Test 27: Chunk indices are sequential across paragraph splits
def test_chunk_indices_sequential():
    # Make section one large enough to split (> 600 tokens)
    para1 = "Para one. " + "Word " * 200
    para2 = "Para two. " + "Word " * 200
    para3 = "Para three. " + "Word " * 200
    para4 = "Para four in section two. " + "Word " * 50
    
    text = f"""## Section One
{para1}

{para2}

{para3}

## Section Two
{para4}"""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Should have at least 4 chunks (3 from Section One + 1 from Section Two)
    assert len(chunks) >= 4, f"Expected at least 4 chunks, got {len(chunks)}"
    
    # Check indices are 0, 1, 2, ...
    for i, chunk in enumerate(chunks):
        assert chunk.metadata.chunk_index == i, \
            f"Expected chunk_index {i}, got {chunk.metadata.chunk_index}"
    print(f"[PASS] Chunk indices sequential: 0 to {len(chunks)-1}")


# Test 28: Introduction section (no heading) works with splitting
def test_intro_section_splits():
    # Make intro large enough to split (> 600 tokens total)
    para1 = "Intro paragraph one. " + "Word " * 250
    para2 = "Intro paragraph two. " + "Word " * 250
    para3 = "Intro paragraph three. " + "Word " * 250
    
    text = f"""{para1}

{para2}

{para3}

## Regular Section
Small content here."""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Should have 3 intro chunks + 1 regular section chunk = 4 total
    assert len(chunks) >= 4, f"Expected at least 4 chunks, got {len(chunks)}"
    
    # First 3 should be Introduction
    for i in range(3):
        assert chunks[i].metadata.section_title == "Introduction", \
            f"Chunk {i} should be Introduction"
    print("[PASS] Introduction section splits by paragraph correctly")


# ============================================================================
# STEP 3: Sentence/Unit Splitting Helpers
# ============================================================================

print("\n" + "=" * 50)
print("STEP 3: Sentence Splitting Helpers")
print("=" * 50)


# Test 29: split_into_sentences basic
def test_split_into_sentences_basic():
    text = "First sentence here. Second sentence here. Third sentence here."
    
    result = split_into_sentences(text)
    
    assert len(result) == 3, f"Expected 3 sentences, got {len(result)}"
    assert "First sentence" in result[0]
    assert "Second sentence" in result[1]
    assert "Third sentence" in result[2]
    print("[PASS] split_into_sentences splits on period-space")


# Test 30: split_into_sentences with different punctuation
def test_split_into_sentences_punctuation():
    text = "Is this a question? Yes it is! And this is a statement."
    
    result = split_into_sentences(text)
    
    assert len(result) == 3, f"Expected 3 sentences, got {len(result)}"
    assert "question?" in result[0]
    assert "Yes it is!" in result[1]
    print("[PASS] split_into_sentences handles ? and !")


# Test 31: split_into_units with list items
def test_split_into_units_list():
    text = """Here is a list:
- First item
- Second item
- Third item"""
    
    result = split_into_units(text)
    
    # Should have: 1 sentence + 3 list items = 4 units
    assert len(result) >= 4, f"Expected at least 4 units, got {len(result)}"
    
    # Check list items are preserved
    list_items = [u for u in result if u.startswith('-')]
    assert len(list_items) == 3, f"Expected 3 list items, got {len(list_items)}"
    print("[PASS] split_into_units handles list items")


# Test 32: split_into_units with numbered list
def test_split_into_units_numbered_list():
    text = """Steps:
1. First step
2. Second step
3. Third step"""
    
    result = split_into_units(text)
    
    # Check numbered items are preserved
    numbered_items = [u for u in result if u[0].isdigit()]
    assert len(numbered_items) == 3, f"Expected 3 numbered items, got {len(numbered_items)}"
    print("[PASS] split_into_units handles numbered lists")


# Test 33: split_into_units with asterisk list
def test_split_into_units_asterisk_list():
    text = """Items:
* Item one
* Item two"""
    
    result = split_into_units(text)
    
    asterisk_items = [u for u in result if u.startswith('*')]
    assert len(asterisk_items) == 2, f"Expected 2 asterisk items, got {len(asterisk_items)}"
    print("[PASS] split_into_units handles asterisk lists")


# Test 34: group_units_by_tokens basic
def test_group_units_basic():
    # Create units that together would exceed 600 tokens
    units = [
        "Sentence one. " + "Word " * 100,  # ~100 tokens
        "Sentence two. " + "Word " * 100,  # ~100 tokens
        "Sentence three. " + "Word " * 100,  # ~100 tokens
        "Sentence four. " + "Word " * 100,  # ~100 tokens
        "Sentence five. " + "Word " * 100,  # ~100 tokens
        "Sentence six. " + "Word " * 100,  # ~100 tokens
        "Sentence seven. " + "Word " * 100,  # ~100 tokens
    ]
    
    result = group_units_by_tokens(units, MAX_TOKENS)
    
    # 700 tokens total, should create 2 groups (each ~350 tokens or so)
    assert len(result) >= 2, f"Expected at least 2 groups, got {len(result)}"
    
    # Each group should be <= MAX_TOKENS (approximately)
    for i, group in enumerate(result):
        tokens = count_tokens(group)
        # Allow some buffer since we don't split mid-unit
        assert tokens <= MAX_TOKENS + 150, f"Group {i} has {tokens} tokens, too large"
    
    print(f"[PASS] group_units_by_tokens creates {len(result)} groups under limit")


# Test 35: group_units respects unit boundaries
def test_group_units_respects_boundaries():
    # Single large unit should stay intact even if > MAX_TOKENS
    large_unit = "This is one very long sentence. " + "Word " * 700
    
    result = group_units_by_tokens([large_unit], MAX_TOKENS)
    
    assert len(result) == 1, "Single unit should stay as single group"
    assert result[0] == large_unit, "Unit should not be modified"
    print("[PASS] group_units_by_tokens never splits mid-unit")


# ============================================================================
# STEP 3: Sentence Splitting Logic in chunk_markdown
# ============================================================================

print("\n" + "=" * 50)
print("STEP 3: Large Paragraph Splits by Sentences")
print("=" * 50)


# Test 36: Large paragraph with multiple sentences splits
def test_large_paragraph_splits_by_sentences():
    # Create a paragraph with many sentences totaling > 600 tokens
    sentences = [f"Sentence number {i}. " + "Word " * 80 for i in range(10)]
    large_para = " ".join(sentences)
    
    text = f"""## Big Section
{large_para}"""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Should have multiple chunks now (was 1 before Step 3)
    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"
    
    # Each chunk should be reasonably sized
    for chunk in chunks:
        # Allow soft limit buffer
        assert chunk.metadata.token_count <= MAX_TOKENS + 150, \
            f"Chunk too large: {chunk.metadata.token_count} tokens"
    
    print(f"[PASS] Large paragraph split into {len(chunks)} sentence-based chunks")


# Test 37: Large paragraph with list splits correctly
def test_large_paragraph_with_list_splits():
    # Create a large list
    list_items = [f"- Item {i} with description. " + "Word " * 60 for i in range(12)]
    large_list = "\n".join(list_items)
    
    text = f"""## List Section
Here are the items:
{large_list}"""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Should split the list into multiple chunks
    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"
    
    # All chunks should have same section_title
    for chunk in chunks:
        assert chunk.metadata.section_title == "List Section"
    
    print(f"[PASS] Large list split into {len(chunks)} chunks (list items as units)")


# Test 38: Single long sentence stays as one chunk (can't split further)
def test_single_long_sentence_stays_whole():
    # One extremely long sentence with no periods
    long_sentence = "This is one very long sentence that just keeps going and going " + "word " * 700
    
    text = f"""## Long Sentence Section
{long_sentence}"""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Can't split mid-sentence, so stays as 1 chunk
    assert len(chunks) == 1, f"Expected 1 chunk (can't split mid-sentence), got {len(chunks)}"
    print(f"[PASS] Single long sentence ({chunks[0].metadata.token_count} tokens) stays whole (can't split)")


# Test 39: Mixed prose and list in large paragraph (all in one paragraph block)
def test_mixed_prose_and_list():
    # Create a single large paragraph with prose and inline list
    # No double newlines so it stays as one paragraph
    prose_start = "First some introductory text. " + "Word " * 350
    list_items = "\n".join([f"- Item {i} with some details here" for i in range(5)])
    prose_end = "And some concluding text here. " + "Word " * 350
    
    # All content in ONE paragraph block (no double newlines)
    large_content = f"{prose_start}\n{list_items}\n{prose_end}"
    
    text = f"""## Mixed Section
{large_content}"""
    
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    
    # Should split since total > 600 tokens
    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"
    print(f"[PASS] Mixed prose/list content creates {len(chunks)} chunks")


# ============================================================================
# STEP 4: Merge Small Chunks
# ============================================================================

print("\n" + "=" * 50)
print("STEP 4: Merge Small Chunks")
print("=" * 50)


# Test 40: merge_small_chunks backward merge
def test_merge_small_backward():
    # (section_title, text) - second chunk is small, same section
    text_chunks = [
        ("Section A", "This is a normal sized chunk. " + "Word " * 80),
        ("Section A", "Tiny."),
    ]
    result = merge_small_chunks(text_chunks)
    assert len(result) == 1, f"Expected 1 chunk after merge, got {len(result)}"
    assert "Tiny." in result[0][1]
    assert result[0][0] == "Section A"
    print("[PASS] Small chunk merges backward into previous (same section)")


# Test 41: merge_small_chunks forward merge (first chunk small)
def test_merge_small_forward():
    text_chunks = [
        ("Section A", "Tiny first."),
        ("Section A", "Bigger second chunk. " + "Word " * 80),
    ]
    result = merge_small_chunks(text_chunks)
    assert len(result) == 1, f"Expected 1 chunk after merge, got {len(result)}"
    assert "Tiny first." in result[0][1]
    assert "Bigger second" in result[0][1]
    assert result[0][0] == "Section A"
    print("[PASS] First chunk small -> merges forward into next")


# Test 42: no merge across sections
def test_merge_same_section_only():
    text_chunks = [
        ("Section A", "Big chunk. " + "Word " * 80),
        ("Section B", "Tiny."),  # different section
        ("Section B", "Another big. " + "Word " * 80),
    ]
    result = merge_small_chunks(text_chunks)
    # Tiny in Section B should merge into "Another big" (same section), not into Section A
    assert len(result) == 2, f"Expected 2 chunks, got {len(result)}"
    assert result[0][0] == "Section A"
    assert result[1][0] == "Section B"
    assert "Tiny." in result[1][1]
    print("[PASS] Small chunk only merges with same section")


# Test 43: first chunk small but next is different section -> no merge
def test_merge_first_small_different_section():
    text_chunks = [
        ("Section A", "Tiny."),
        ("Section B", "Content. " + "Word " * 80),
    ]
    result = merge_small_chunks(text_chunks)
    # Cannot merge (different sections), so both stay
    assert len(result) == 2, f"Expected 2 chunks (no merge across section), got {len(result)}"
    print("[PASS] First chunk small but next different section -> no merge")


# Test 44: chunk_markdown produces fewer chunks when small chunks exist
def test_chunk_markdown_merges_small():
    # Two small sections that would each be one chunk; second is tiny
    text = """## First
Short content here.

## Second
Tiny."""
    chunks = chunk_markdown(text, doc_id="test", sourcename="test.md")
    # "Second" is tiny - but it's the only chunk in its section, so no sibling to merge with
    # So we get 2 chunks. To test merge we need two chunks in same section.
    # Instead: one section with two paragraphs, first big enough, second tiny
    text2 = """## Only Section
First paragraph with enough content. """ + "Word " * 80 + """

Second tiny."""
    chunks2 = chunk_markdown(text2, doc_id="test", sourcename="test.md")
    # Should merge "Second tiny" into first paragraph (backward)
    assert len(chunks2) == 1, f"Expected 1 chunk after merging small, got {len(chunks2)}"
    assert "Second tiny" in chunks2[0].text
    print("[PASS] chunk_markdown merges small chunk into previous (same section)")


# Test 45: consecutive small chunks merge into one
def test_consecutive_small_merge():
    text_chunks = [
        ("Section A", "One. " + "Word " * 50),  # ~50 tokens, under 100
        ("Section A", "Two."),
        ("Section A", "Three."),
    ]
    result = merge_small_chunks(text_chunks)
    # First stays (or gets "Two" merged in?), then "Two" and "Three" merge backward
    # Actually: first chunk has ~50 tokens < 100, so it's small. So we try to merge backward - no previous. Then merge forward - next is same section, so we merge first into second -> (One+Two). Then we have (One+Two) and "Three". Three is small, merge into (One+Two). So one chunk.
    assert len(result) == 1, f"Expected 1 chunk after merging consecutive small, got {len(result)}"
    assert "One" in result[0][1] and "Two" in result[0][1] and "Three" in result[0][1]
    print("[PASS] Consecutive small chunks in same section merge into one")


# Run all tests
def run_all_tests():
    # ========================================
    # STEP 1: split_by_headings tests
    # ========================================
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
    
    # chunk_markdown basic tests
    test_chunk_markdown_basic()
    test_heading_removed_from_content()
    test_chunk_id_derived()
    test_token_count()
    test_url_optional()
    
    # ========================================
    # STEP 2: Helper function tests
    # ========================================
    test_remove_heading_line_basic()
    test_remove_heading_line_preserves_content()
    test_remove_heading_line_no_heading()
    test_split_by_paragraphs_basic()
    test_split_by_paragraphs_multiple_newlines()
    test_split_by_paragraphs_filters_empty()
    test_count_tokens()
    
    # STEP 2: Paragraph splitting logic tests
    test_small_section_single_chunk()
    test_large_section_splits_by_paragraph()
    test_paragraph_chunks_same_section_title()
    test_chunk_indices_sequential()
    test_intro_section_splits()
    
    # ========================================
    # STEP 3: Helper function tests
    # ========================================
    test_split_into_sentences_basic()
    test_split_into_sentences_punctuation()
    test_split_into_units_list()
    test_split_into_units_numbered_list()
    test_split_into_units_asterisk_list()
    test_group_units_basic()
    test_group_units_respects_boundaries()
    
    # STEP 3: Sentence splitting logic tests
    test_large_paragraph_splits_by_sentences()
    test_large_paragraph_with_list_splits()
    test_single_long_sentence_stays_whole()
    test_mixed_prose_and_list()
    
    # ========================================
    # STEP 4: Merge small chunks tests
    # ========================================
    test_merge_small_backward()
    test_merge_small_forward()
    test_merge_same_section_only()
    test_merge_first_small_different_section()
    test_chunk_markdown_merges_small()
    test_consecutive_small_merge()
    
    print("\n" + "="*50)
    print("All Step 1, 2, 3 & 4 tests passed! [PASS]")
    print("="*50)


# Execute tests
if __name__ == "__main__":
    run_all_tests()

