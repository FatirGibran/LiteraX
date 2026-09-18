from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Telegram Bot
    bot_token: Optional[str] = None

    # Database & Redis
    database_url: str = "postgresql+asyncpg://literax:literax_secret@localhost:5432/literax_db"
    redis_url: str = "redis://localhost:6379/0"

    # Open Access Polite Pools
    openalex_email: str = "researcher@university.ac.id"
    crossref_mailto: str = "researcher@university.ac.id"

    # Subscribed Providers
    semantic_scholar_api_key: Optional[str] = None
    scopus_api_key: Optional[str] = None
    scopus_insttoken: Optional[str] = None

    # AI & LLM settings
    llm_provider: str = "gemini"
    llm_api_key: Optional[str] = None
    llm_model: str = "gemini-1.5-flash"
    llm_base_url: Optional[str] = None

    # App Settings
    log_level: str = "INFO"
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
