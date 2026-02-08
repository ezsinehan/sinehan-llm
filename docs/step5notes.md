Step 5: Embed chunks locally.

- Embedding model is local (BAAI/bge-small-en-v1.5 via sentence-transformers) for cost control and latency (step1 notes).
- Config: embedding_model_name and embedding_dimension (384) in app/config (step2 notes). Qdrant collection uses embedding_dimension.
- Text to embed per chunk: section_title + "\n\n" + chunk.text (Option B from step4 notes). Chunk text does not include the ## heading line; combining at embed time gives the vector full context.
- Implementation: app/services/embedder.py. Model loaded on first use (lazy). embed_text(s) for raw strings; text_to_embed_for_chunk(chunk) builds the combined string; embed_chunks(chunks) returns List[List[float]] in same order as chunks.
- Manual test: run `python scripts/manual_test_chunking.py` (no --no-embed). Embeds all chunks and writes manual_test_embeddings.json. Install sentence-transformers if needed: pip install sentence-transformers.

---
[AI-GENERATED SUMMARY]

Step 5 Decisions - Embed chunks locally:
- Library: sentence-transformers (model from config.embedding_model_name, e.g. BAAI/bge-small-en-v1.5)
- Dimension: config.embedding_dimension (384 for bge-small-en-v1.5); used when creating Qdrant collection
- Input per chunk: section_title + "\n\n" + chunk.text (no ## in chunk.text; heading in metadata only)
- API: embed_text(str), embed_texts(List[str]), embed_chunks(List[Chunk]) -> List[List[float]]; text_to_embed_for_chunk(Chunk) for the combined string
- Model loaded once on first embed (lazy), stored in module-level _model
- Output: list of float vectors, one per chunk, same order as input chunks
- Manual test: scripts/manual_test_chunking.py (full pipeline clean->chunk->embed); writes manual_test_embeddings.json; use --no-embed to skip embedding step