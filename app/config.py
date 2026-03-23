from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Config (Ollama)
    ollama_url: str = "http://localhost:11434"
    ollama_model_name: str = "qwen2.5:7b"
    ollama_max_tokens: int = 8192

    # Vector DB Config (local Docker or Qdrant Cloud)
    qdrant_url: str
    qdrant_api_key: str = ""

    # Embedding Model Config
    embedding_model_name: str
    embedding_dimension: int = 384

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

