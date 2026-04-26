"""Language API route — list supported languages."""

from fastapi import APIRouter
from app.models.schemas import LANGUAGE_NAMES

router = APIRouter(prefix="/api", tags=["language"])


@router.get("/languages")
async def get_languages() -> dict:
    """Return all supported languages."""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in LANGUAGE_NAMES.items()
        ],
        "default": "en",
        "priority": ["hi", "bn", "ta", "te", "kn", "sat", "uk"],
    }
