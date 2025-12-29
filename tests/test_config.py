# .\venv\Scripts\python.exe tests/test_config.py
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings

# Test that settings loaded correctly
print("Config loaded successfully!")
print(f"Gemini API Key: {settings.gemini_api_key[:10]}..." if len(settings.gemini_api_key) > 10 else "  API key too short")
print(f"Gemini Model: {settings.gemini_model_name}")
print(f"Qdrant URL: {settings.qdrant_url}")
print(f"Qdrant API Key: {settings.qdrant_api_key[:10]}..." if len(settings.qdrant_api_key) > 10 else "  API key too short")
print(f"Embedding Model: {settings.embedding_model_name}")
print(f"Embedding Dimension: {settings.embedding_dimension} (type: {type(settings.embedding_dimension).__name__})")

