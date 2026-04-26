"""Shared API dependencies."""

from fastapi import Depends
from app.core.security import rate_limit_dependency
from app.core.config import get_settings, Settings


async def get_current_settings() -> Settings:
    """Dependency to get app settings."""
    return get_settings()
