# tests/run_all_tests.py
"""Run all test modules. From project root with venv: python tests/run_all_tests.py"""
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
tests_dir = Path(__file__).resolve().parent

# Test files that have if __name__ == "__main__" and can be run as scripts
TEST_FILES = [
    "test_chunkmodel.py",
    "test_text_cleaner.py",
    "test_chunker.py",
    "test_embedder.py",
    "test_text_extractor.py",
    "test_vector_store.py",
]

def main():
    python = sys.executable
    failed = []
    for name in TEST_FILES:
        path = tests_dir / name
        if not path.exists():
            continue
        print("\n" + "=" * 60)
        print(f"Running {name}")
        print("=" * 60)
        result = subprocess.run(
            [python, str(path)],
            cwd=str(project_root),
        )
        if result.returncode != 0:
            failed.append(name)
    if failed:
        print("\n" + "=" * 60)
        print("FAILED:", ", ".join(failed))
        print("=" * 60)
        sys.exit(1)
    print("\n" + "=" * 60)
    print("All test files passed.")
    print("=" * 60)

if __name__ == "__main__":
    main()
