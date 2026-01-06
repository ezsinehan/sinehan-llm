# Imports BaseModel from pydantic(library for data validation using python type hints, checking types, validates data, and converts inputs to the expected types), BaseModel is a base class for defining data models inheriting from it gives automatic validation of fields, type conversion, JSON serialization/deserilization, clean error mesages
# Optional from typing module (provides type hints for python) providing the optional type
from pydantic import BaseModel
from typing import Optional

class ChunkMetadata(BaseModel):
    doc_id: str # human-readable, stable identifier
    chunk_index: int # sequential position
    section_title: str # heading this chunk belongs too
    url: Optional[str] # verification link
    token_count: int # number of tokens
    source_name: str # og filename

    # @property is a decorator that turns a method into a property, python calls property() and the method is wrappedso it can accessed like an attribute no ()
    @property
    def chunk_id(self) -> str:
        """Derived chunk_id: {doc_id}_{chunk_index}"""
        return f"{self.doc_id}_{self.chunk_index}"

class Chunk(BaseModel):
    text: str # the chunk text w/ markdown
    metadata: ChunkMetadata