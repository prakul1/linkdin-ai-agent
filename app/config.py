"""
Central configuration. Loads from .env file.
Type-safe, validated, autocompletes in IDE.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    # App
    app_name: str = "LinkedIn AI Agent"
    app_env: str = "development"
    debug: bool = True
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    # Database
    database_url: str = "sqlite:///./data/app.db"
    # Vector DB
    chroma_persist_dir: str = "./data/chroma"
    # Storage
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 10
    # LinkedIn
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = ""
    # Cost controls
    max_tokens_per_request: int = 800
    daily_token_limit: int = 50000
    enable_token_tracking: bool = True
@lru_cache
def get_settings() -> Settings:
    return Settings()
settings = get_settings()