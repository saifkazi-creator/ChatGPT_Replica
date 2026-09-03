from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env path relative to this file so it works regardless of cwd
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Gemini is used for both LLM and embeddings
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.6-flash"

    WEB_SEARCH_API_KEY: str = ""

    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 768

    MEM0_API_KEY: str = ""


settings = Settings()
