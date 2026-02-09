"""
Manual test for step 8/9: call POST /answer and print answer + citations.
Requires the API server running (uvicorn app.main:app), Qdrant with data,
and GEMINI_API_KEY + GEMINI_MODEL_NAME in .env.

Usage (from project root, with venv activated):
  python scripts/manual_test_answer.py
  python scripts/manual_test_answer.py "Your question here"
  python scripts/manual_test_answer.py "Your question" --top-k 3
  python scripts/manual_test_answer.py --url http://localhost:8000
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def call_answer(url: str, question: str, top_k: int) -> dict:
    if HAS_REQUESTS:
        r = requests.post(
            f"{url.rstrip('/')}/answer",
            json={"question": question, "top_k": top_k},
            headers={"Content-Type": "application/json"},
            timeout=90,
        )
        r.raise_for_status()
        return r.json()
    import urllib.request
    req = urllib.request.Request(
        f"{url.rstrip('/')}/answer",
        data=json.dumps({"question": question, "top_k": top_k}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Manual test: POST /answer and print answer + citations.")
    parser.add_argument(
        "question",
        nargs="?",
        default="What is this document about?",
        help="Question to send (default: What is this document about?)",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Number of chunks to use (default: 3)")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of API (default: http://localhost:8000)")
    args = parser.parse_args()

    print("=" * 70)
    print("STEP 8/9 MANUAL TEST: Answer endpoint (question -> LLM -> answer + citations)")
    print("=" * 70)
    print(f"URL:      {args.url}")
    print(f"Question: {args.question!r}")
    print(f"top_k:    {args.top_k}")
    print()

    try:
        data = call_answer(args.url, args.question, args.top_k)
    except Exception as e:
        print("Request failed:", e)
        if not HAS_REQUESTS:
            print("Install requests for clearer errors: pip install requests")
        sys.exit(1)

    answer = data.get("answer", "")
    citations = data.get("citations", [])

    print("ANSWER")
    print("-" * 60)
    print(answer)
    print()
    print(f"CITATIONS ({len(citations)} source(s))")
    print("-" * 60)
    for i, c in enumerate(citations, 1):
        print(f"  [{i}] {c.get('section_title')} | doc_id={c.get('doc_id')} | {c.get('source_name')}")
        if c.get("url"):
            print(f"      url: {c.get('url')}")
    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
