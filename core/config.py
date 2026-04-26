"""Application configuration using environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    APP_NAME: str = "DHARMA-NYAYA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Gemma / Gemini API
    GEMINI_API_KEY: str = ""
    GEMMA_MODEL: str = "gemma-4-31b-it"
    GEMMA_THINKING_LEVEL: str = "HIGH"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,pdf"
    UPLOAD_DIR: str = "uploads"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 30

    # Default language
    DEFAULT_LANGUAGE: str = "en"

    # Google Search grounding (Chat / Spot-the-Trap / Predict)
    # Gemma 4 31B fully supports the `googleSearch` tool — when enabled, the
    # model itself runs Google Search during generation and verified source
    # URLs come back in `grounding_metadata.grounding_chunks`.
    USE_GOOGLE_SEARCH_GROUNDING: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
