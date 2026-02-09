"""
Manual test: run the full pipeline (clean -> chunk -> embed) on a markdown file.
Shows chunk summary, full chunk text, then embedding summary and saves embeddings for inspection.
Usage (from project root, with venv activated):
  python scripts/manual_test_chunking.py
  python scripts/manual_test_chunking.py path/to/your.md
  python scripts/manual_test_chunking.py path/to/your.md --no-embed   # skip embedding step
  python scripts/manual_test_chunking.py path/to/your.md --no-store  # embed but do not store in Qdrant
"""
import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services.text_cleaner import clean_text
from app.services.chunker import chunk_markdown, MAX_TOKENS, MIN_TOKENS


def main():
    parser = argparse.ArgumentParser(description="Run clean -> chunk -> embed on a markdown file.")
    parser.add_argument("md_file", nargs="?", default=None, help="Path to .md file (default: sample_doc.md)")
    parser.add_argument("--no-embed", action="store_true", help="Skip embedding step (chunk only)")
    parser.add_argument("--no-store", action="store_true", help="Skip storing in Qdrant (only when embedding)")
    args = parser.parse_args()

    md_path = Path(args.md_file) if args.md_file else project_root / "sample_doc.md"

    if not md_path.exists():
        print(f"File not found: {md_path}")
        sys.exit(1)

    raw = md_path.read_text(encoding="utf-8")
    cleaned = clean_text(raw)
    doc_id = "sample-doc"
    sourcename = md_path.name
    url = "https://example.com/sample-doc"

    chunks = chunk_markdown(cleaned, doc_id=doc_id, sourcename=sourcename, url=url)

    # --- Summary ---
    print("=" * 70)
    print("CHUNKING PIPELINE: manual test")
    print("=" * 70)
    print(f"Input:        {md_path}")
    print(f"doc_id:       {doc_id}")
    print(f"source_name:  {sourcename}")
    print(f"url:          {url}")
    print(f"Thresholds:   MAX_TOKENS={MAX_TOKENS}  MIN_TOKENS={MIN_TOKENS}")
    print()

    # Per-section stats (how many chunks per section)
    by_section = defaultdict(list)
    for c in chunks:
        by_section[c.metadata.section_title].append(c.metadata.token_count)

    # Section order as in document
    seen = set()
    section_order = []
    for c in chunks:
        s = c.metadata.section_title
        if s not in seen:
            seen.add(s)
            section_order.append(s)

    print("SUMMARY BY SECTION")
    print("-" * 70)
    print(f"{'Section':<42} {'Chunks':>8} {'Tokens':>12}")
    print("-" * 70)
    for section in section_order:
        counts = by_section[section]
        tok_range = f"{min(counts)}-{max(counts)}" if len(counts) > 1 else str(counts[0])
        n = len(counts)
        note = " (split)" if n > 1 else ""
        print(f"{section[:40]:<42} {n:>8} {tok_range:>12}{note}")
    print("-" * 70)
    print(f"Total chunks: {len(chunks)}")
    print()

    # What happened (which sections were split)
    print("WHAT HAPPENED")
    print("-" * 70)
    for section in section_order:
        n = len(by_section[section])
        if n > 1:
            print(f"  Section {section!r} was split into {n} chunks (content exceeded {MAX_TOKENS} tokens).")
        else:
            t = by_section[section][0]
            if t < MIN_TOKENS:
                print(f"  Section {section!r}: 1 chunk, {t} tokens (under {MIN_TOKENS}; would merge if same-section sibling existed).")
            else:
                print(f"  Section {section!r}: 1 chunk, {t} tokens.")
    print()

    # Full chunk listing
    print("=" * 70)
    print("CHUNKS (full text)")
    print("=" * 70)

    for c in chunks:
        m = c.metadata
        print()
        print("-" * 70)
        print(f"CHUNK {m.chunk_index}  |  id={m.chunk_id}  |  section={m.section_title!r}  |  tokens={m.token_count}")
        print("-" * 70)
        print(c.text)
        print()

    # --- Embedding (optional) ---
    if not args.no_embed:
        try:
            from app.services.embedder import embed_chunks
        except ModuleNotFoundError as e:
            if "sentence_transformers" in str(e):
                print("=" * 70)
                print("EMBEDDING SKIPPED: sentence-transformers not installed")
                print("Install with:  pip install sentence-transformers")
                print("Then run this script again.")
                print("=" * 70)
                sys.exit(1)
            raise
        from app.config import settings

        print("=" * 70)
        print("EMBEDDING")
        print("=" * 70)
        print(f"Model: {settings.embedding_model_name}")
        print(f"Dimension: {settings.embedding_dimension}")
        print("Embedding chunks (section_title + text per chunk)...")
        vectors = embed_chunks(chunks)
        print(f"Done. {len(vectors)} vectors, each length {len(vectors[0]) if vectors else 0}")
        if vectors:
            preview = vectors[0][:5]
            print(f"First vector (first 5 values): {[round(x, 4) for x in preview]}")
        print()

        # Save for inspection
        out_path = project_root / "manual_test_embeddings.json"
        payload = {
            "doc_id": doc_id,
            "source_name": sourcename,
            "url": url,
            "model": settings.embedding_model_name,
            "dimension": settings.embedding_dimension,
            "chunks": [
                {
                    "chunk_id": c.metadata.chunk_id,
                    "section_title": c.metadata.section_title,
                    "chunk_index": c.metadata.chunk_index,
                    "token_count": c.metadata.token_count,
                    "text_preview": c.text[:300] + ("..." if len(c.text) > 300 else ""),
                    "embedding": vectors[i],
                }
                for i, c in enumerate(chunks)
            ],
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved embeddings to {out_path}")
        print()

        # --- Store in Qdrant (step 6) ---
        if not args.no_store:
            try:
                from app.services.vector_store import (
                    COLLECTION_NAME,
                    ensure_collection,
                    delete_by_doc_id,
                    upsert_chunks,
                )
                ensure_collection(COLLECTION_NAME)
                delete_by_doc_id(doc_id, COLLECTION_NAME)
                upsert_chunks(chunks, vectors, COLLECTION_NAME)
                print("=" * 70)
                print("QDRANT STORE")
                print("=" * 70)
                print(f"Collection: {COLLECTION_NAME}")
                print(f"Deleted existing points for doc_id={doc_id!r}, upserted {len(chunks)} points.")
                print()
            except Exception as e:
                print("=" * 70)
                print("QDRANT STORE FAILED")
                print("=" * 70)
                print(f"Error: {e}")
                print("Check QDRANT_URL and QDRANT_API_KEY in .env. Use --no-store to skip.")
                print()
    else:
        print("(Embedding skipped: use without --no-embed to run full pipeline)")
        print()

    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
