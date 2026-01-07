import tiktoken
import re
from typing import List, Optional, Tuple
from app.models.chunk import Chunk, ChunkMetadata

# Initialize tokenizer once at module level (expensive operation, only do once)
tokenizer = tiktoken.get_encoding("cl100k_base")

# Soft maximum token threshold - sections/paragraphs above this get split
# "Soft" means slightly over (e.g., 650) is okay to preserve semantic meaning
MAX_TOKENS = 600

# EMBEDDING NOTE: chunk.text does NOT include the heading line.
# When embedding, combine: f"{chunk.metadata.section_title}\n\n{chunk.text}"
# This keeps storage clean while ensuring embeddings have full context.


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in text using tiktoken.
    
    Args:
        text: The text to count tokens for
        
    Returns:
        Number of tokens
    """
    return len(tokenizer.encode(text))


def remove_heading_line(section_content: str) -> str:
    """
    Remove the ## heading line from section content.
    
    Since section_title is stored in metadata, we don't need the heading
    in the chunk text. This avoids duplication - citations work via metadata.
    
    Args:
        section_content: Full section text (may start with ## heading)
        
    Returns:
        Section text with heading line removed, stripped of leading whitespace
    """
    # Pattern matches a line starting with ## at the beginning of the string
    # ^        : start of string
    # ##       : literal ##
    # [^\n]*   : any characters except newline (the heading text)
    # \n?      : optional newline after heading
    heading_pattern = re.compile(r'^##[^\n]*\n?')
    
    # Remove the heading line and strip any resulting leading whitespace
    result = heading_pattern.sub('', section_content)
    return result.strip()


def split_by_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs using double newlines as delimiter.
    
    Args:
        text: Text to split into paragraphs
        
    Returns:
        List of paragraph strings (empty paragraphs filtered out)
    """
    # Split on two or more consecutive newlines
    # \n{2,} matches \n\n, \n\n\n, etc.
    paragraphs = re.split(r'\n{2,}', text)
    
    # Filter out empty paragraphs and strip whitespace from each
    # This handles cases like "\n\n\n\n" which would create empty strings
    return [p.strip() for p in paragraphs if p.strip()]


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


def chunk_markdown(
    text: str,
    doc_id: str,
    sourcename: str,
    url: Optional[str] = None
) -> List[Chunk]:
    """
    Main chunking function:
    1. Split by headings [DONE]
    2. For each section: check size, if > 600 tokens split by paragraph [DONE]
    3. If paragraph > 600 tokens: split by sentences [TODO]
    4. Merge chunks < 100 tokens with previous (or next if first) [TODO]
    """
    # STEP 1: Split by ## headings
    sections = split_by_headings(text)
    
    # Collect all text chunks before creating Chunk objects
    # Each item: (section_title, chunk_text)
    text_chunks: List[Tuple[str, str]] = []
    
    for section_title, section_content in sections:
        # Remove the ## heading line from content (Option B)
        # Heading info is preserved in section_title metadata
        # "Introduction" sections don't have a heading line to remove
        if section_title != "Introduction":
            content = remove_heading_line(section_content)
        else:
            content = section_content.strip()
        
        # Skip if content is empty after removing heading
        if not content:
            continue
        
        # STEP 2: Check token count and split if needed
        token_count = count_tokens(content)
        
        if token_count <= MAX_TOKENS:
            # Section is small enough - keep as single chunk
            text_chunks.append((section_title, content))
        else:
            # Section too large - split by paragraphs
            paragraphs = split_by_paragraphs(content)
            
            if len(paragraphs) == 0:
                # Edge case: content exists but no paragraphs (shouldn't happen)
                text_chunks.append((section_title, content))
            elif len(paragraphs) == 1:
                # Only one paragraph but it's > 600 tokens
                # Step 3 will handle splitting by sentences
                # For now, keep as single chunk
                text_chunks.append((section_title, content))
            else:
                # Multiple paragraphs - each becomes a chunk
                # All chunks inherit the same section_title
                for paragraph in paragraphs:
                    if paragraph:  # Skip empty paragraphs
                        text_chunks.append((section_title, paragraph))
    
    # Convert text chunks to Chunk objects with metadata
    chunks: List[Chunk] = []
    
    for chunk_index, (section_title, chunk_text) in enumerate(text_chunks):
        token_count = count_tokens(chunk_text)
        
        metadata = ChunkMetadata(
            doc_id=doc_id,
            chunk_index=chunk_index,
            section_title=section_title,
            url=url,
            token_count=token_count,
            source_name=sourcename
        )
        
        chunk = Chunk(text=chunk_text, metadata=metadata)
        chunks.append(chunk)
    
    return chunks