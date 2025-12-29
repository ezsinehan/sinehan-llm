from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Config
    gemini_api_key: str
    gemini_model_name: str

    # Vector DB Config
    qdrant_url: str
    qdrant_api_key: str

    # Embedding Model Config
    embedding_model_name: str
    embedding_dimension: int = 384

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

