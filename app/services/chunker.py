import tiktoken
import re
from typing import List, Optional, Tuple
from app.models.chunk import Chunk, ChunkMetadata

# Initialize tokenizer once at module level (expensive operation, only do once)
tokenizer = tiktoken.get_encoding("cl100k_base")


def split_by_headings(text: str) -> List[Tuple[str, str]]:
    """
    Split markdown text into sections based on ## headings.
    
    Args:
        text: The full markdown text to split
        
    Returns:
        List of tuples: (section_title, section_content)
        - section_title: plain text heading (no ## prefix)
        - section_content: all text under that heading (including the heading line)
    
    Rules:
        - ## headings are the primary split points (# is usually project title)
        - Content before first ## gets synthetic title "Introduction"
        - Empty sections (heading with no content) are dropped
    """
    
    # Regex pattern to match ## headings at the start of a line
    # ^        : start of line (with re.MULTILINE flag)
    # ##       : literal two hash characters
    # \s+      : one or more whitespace (space between ## and title)
    # (.+)     : capture group - one or more characters (the heading text)
    # $        : end of line
    heading_pattern = re.compile(r'^##\s+(.+)$', re.MULTILINE)
    
    # Find all ## headings and their positions in the text
    # finditer returns an iterator of Match objects with:
    #   - .group(0): full match "## Heading Text"
    #   - .group(1): captured group "Heading Text" (just the title)
    #   - .start(): position where match begins
    #   - .end(): position where match ends
    matches = list(heading_pattern.finditer(text))
    
    sections: List[Tuple[str, str]] = []
    
    # Handle content before the first ## heading (if any)
    if matches:
        # Get text from start to first heading
        first_heading_pos = matches[0].start()
        intro_content = text[:first_heading_pos].strip()
        
        # Only add intro section if there's actual content
        # (not just whitespace or empty)
        if intro_content:
            sections.append(("Introduction", intro_content))
    else:
        # No ## headings found at all - entire text is one section
        # This handles edge case of markdown without ## structure
        stripped = text.strip()
        if stripped:
            sections.append(("Introduction", stripped))
        return sections
    
    # Process each ## heading and its content
    for i, match in enumerate(matches):
        # Extract the heading title (captured group, no ## prefix)
        section_title = match.group(1).strip()
        
        # Determine where this section's content ends:
        # - If there's a next heading, content ends at start of next heading
        # - If this is the last heading, content ends at end of document
        if i + 1 < len(matches):
            # There's another heading after this one
            next_heading_pos = matches[i + 1].start()
            section_content = text[match.start():next_heading_pos].strip()
        else:
            # This is the last heading - take rest of document
            section_content = text[match.start():].strip()
        
        # Drop empty sections (heading exists but no content after it)
        # A section is "empty" if it only contains the heading line itself
        # We check if content after removing the heading line is empty
        content_after_heading = text[match.end():next_heading_pos if i + 1 < len(matches) else len(text)].strip()
        
        if content_after_heading:
            # Section has actual content, keep it
            sections.append((section_title, section_content))
        # else: section is empty (just a heading), drop it per requirements
    
    return sections


# ============================================================================
# MAIN CHUNKING FUNCTION (Steps 2-5 to be implemented)
# ============================================================================

def chunk_markdown(
    text: str,
    doc_id: str,
    sourcename: str,
    url: Optional[str] = None
) -> List[Chunk]:
    """
    Main chunking function:
    1. Split by headings ✓
    2. For each section: check size
    3. If > 600 tokens: split by paragraph
    4. If paragraph > 600 tokens: split by sentences
    5. Merge chunks < 100 tokens with previous (or next if first)
    """
    # STEP 1: Split by ## headings
    sections = split_by_headings(text)
    
    # For now, create one chunk per section (Steps 2-5 will refine this)
    chunks: List[Chunk] = []
    
    for chunk_index, (section_title, section_content) in enumerate(sections):
        # Count tokens using tiktoken
        token_count = len(tokenizer.encode(section_content))
        
        # Create metadata for this chunk
        metadata = ChunkMetadata(
            doc_id=doc_id,
            chunk_index=chunk_index,
            section_title=section_title,
            url=url,
            token_count=token_count,
            source_name=sourcename
        )
        
        # Create the chunk with text and metadata
        chunk = Chunk(text=section_content, metadata=metadata)
        chunks.append(chunk)
    
    return chunks