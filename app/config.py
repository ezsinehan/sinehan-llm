from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Config (Gemini)
    gemini_api_key: str
    # Use a supported model: gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash, gemini-3-flash-preview
    gemini_model_name: str = "gemini-2.5-flash"
    gemini_max_output_tokens: int = 8192  # raise if answers are cut off (was 1024)

    # Vector DB Config (Qdrant Cloud: set QDRANT_URL and QDRANT_API_KEY in .env)
    qdrant_url: str
    qdrant_api_key: str

    # Embedding Model Config
    embedding_model_name: str
    embedding_dimension: int = 384

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

