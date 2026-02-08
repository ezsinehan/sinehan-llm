"""
Manual test: run the full pipeline (clean -> chunk) on a markdown file and print chunks with metadata.
Shows a summary table, then each chunk in full so you can see how large sections are split.
Usage (from project root, with venv activated):
  python scripts/manual_test_chunking.py
  python scripts/manual_test_chunking.py path/to/your.md
"""
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services.text_cleaner import clean_text
from app.services.chunker import chunk_markdown, MAX_TOKENS, MIN_TOKENS


def main():
    # Default to sample_doc.md in project root; allow override via argv
    if len(sys.argv) > 1:
        md_path = Path(sys.argv[1])
    else:
        md_path = project_root / "sample_doc.md"

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

    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
