"""
Delete the entire Qdrant collection (all chunks). Run from project root with venv.
After this, run manual_test_chunking.py or POST /ingest to repopulate.

Usage: python scripts/delete_all_qdrant.py
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services.vector_store import _get_client, COLLECTION_NAME


def main():
    client = _get_client()
    if not client.collection_exists(COLLECTION_NAME):
        print(f"Collection {COLLECTION_NAME!r} does not exist. Nothing to delete.")
        return
    client.delete_collection(COLLECTION_NAME)
    print(f"Deleted collection {COLLECTION_NAME!r}. Run manual_test_chunking.py or /ingest to repopulate.")


if __name__ == "__main__":
    main()
