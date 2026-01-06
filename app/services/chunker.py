import tiktoken
import re
from typing import List, Optional
from app.models.chunk import Chunk, ChunkMetadata

# Initialize tokenizer once
tokenizer = tiktoken.get_encoding("cl100k_base")

def chunk_markdown(
    text: str,
    doc_id: str,
    sourcename: str,
    url: Optional[str] = None
) -> List[Chunk]:
    """
    Main chunking function:
    1. Split by headings
    2. For each section: check size
    3. If > 600 tokens: split by paragraph
    4. If paragraph > 600 tokens: split by sentences
    5. Merge chunks < 100 tokens with previous (or next if first)
    """
    # Implementation here
    pass