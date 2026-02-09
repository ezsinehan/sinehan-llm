"""
Manual test for step 7: call POST /query and print retrieved chunks.
Requires the API server to be running (uvicorn app.main:app) and Qdrant to have data
(run scripts/manual_test_chunking.py once without --no-store).

Usage (from project root, with venv activated):
  python scripts/manual_test_query.py
  python scripts/manual_test_query.py "Your question here"
  python scripts/manual_test_query.py "Your question" --top-k 5
  python scripts/manual_test_query.py --url http://localhost:8000
"""
import argparse
import json
import sys
from pathlib import Path

# Prefer requests if available; else fall back to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def call_query(url: str, question: str, top_k: int) -> dict:
    if HAS_REQUESTS:
        r = requests.post(
            f"{url.rstrip('/')}/query",
            json={"question": question, "top_k": top_k},
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    # Fallback: urllib
    import urllib.request
    import urllib.error
    req = urllib.request.Request(
        f"{url.rstrip('/')}/query",
        data=json.dumps({"question": question, "top_k": top_k}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Manual test: POST /query and print chunks.")
    parser.add_argument(
        "question",
        nargs="?",
        default="What is this document about?",
        help="Question to send (default: What is this document about?)",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Number of chunks to return (default: 3)")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of API (default: http://localhost:8000)")
    args = parser.parse_args()

    print("=" * 70)
    print("STEP 7 MANUAL TEST: Query endpoint")
    print("=" * 70)
    print(f"URL:      {args.url}")
    print(f"Question: {args.question!r}")
    print(f"top_k:    {args.top_k}")
    print()

    try:
        data = call_query(args.url, args.question, args.top_k)
    except Exception as e:
        print("Request failed:", e)
        if not HAS_REQUESTS:
            print("Install requests for clearer errors: pip install requests")
        sys.exit(1)

    chunks = data.get("chunks", [])
    print(f"Retrieved {len(chunks)} chunk(s):")
    print()
    for i, c in enumerate(chunks, 1):
        print("-" * 60)
        print(f"Chunk {i}  score={c.get('score', 'N/A')}  doc_id={c.get('doc_id')}  chunk_id={c.get('chunk_id')}")
        print(f"Section: {c.get('section_title')}")
        text = c.get("text", "")
        preview = text[:300] + ("..." if len(text) > 300 else "")
        print(preview)
        print()
    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
