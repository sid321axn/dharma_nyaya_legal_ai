"""Case management API route."""

from fastapi import APIRouter, HTTPException
from app.models.schemas import Case
from app.models.database import get_case, list_cases

router = APIRouter(prefix="/api", tags=["case"])


@router.get("/case/{case_id}")
async def get_case_by_id(case_id: str) -> dict:
    """Get case details by ID."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/cases")
async def get_all_cases() -> list[dict]:
    """List all cases."""
    return list_cases()
