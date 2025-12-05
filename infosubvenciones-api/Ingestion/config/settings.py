"""Settings and configuration management using pydantic-settings."""
from typing import Optional
import os

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables are loaded from .env file if present.
    """

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API Keys
    gemini_api_key: str
    openai_api_key: Optional[str] = None  # Optional, we'll use Gemini for embeddings

    # InfoSubvenciones API
    infosubvenciones_api_base_url: str = "https://www.infosubvenciones.es/bdnstrans/GE/es"
    infosubvenciones_api_timeout: int = 30

    # PDF Processing
    pdf_downloads_dir: str = r"D:\IT workspace\infosubvenciones-api\downloads"
    pdf_max_size_mb: int = 50  # Maximum PDF size in MB

    # Celery
    celery_broker_url: Optional[str] = None  # Defaults to redis_url if not set
    celery_result_backend: Optional[str] = None  # Defaults to redis_url if not set

    # LLM Settings (Gemini)
    gemini_model: str = Field(
        default="gemini-2.5-flash-lite",
        alias="GEMINI_MODEL",
        description="Gemini model name configurable via .env"
    )
    gemini_embedding_model: str = "text-embedding-004"
    embedding_dimensions: int = 768  # text-embedding-004 dimensions
    gemini_max_retries: int = 3
    gemini_timeout: int = 60

    # Embedding Settings
    embedding_batch_size: int = 100

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set Celery URLs to redis_url if not explicitly set
        if not self.celery_broker_url:
            self.celery_broker_url = self.redis_url
        if not self.celery_result_backend:
            self.celery_result_backend = self.redis_url


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
