"""Action generation API route."""

from fastapi import APIRouter, Depends
from app.models.schemas import ActionRequest, ActionResponse
from app.agents.action_agent import action_agent
from app.core.security import rate_limit_dependency, sanitize_input

router = APIRouter(prefix="/api/action", tags=["action"])


@router.post("/generate", response_model=ActionResponse,
             dependencies=[Depends(rate_limit_dependency)])
async def generate_action(request: ActionRequest) -> ActionResponse:
    """Generate a legal document (complaint, notice, RTI, etc.)."""
    request.context = sanitize_input(request.context)
    return await action_agent.generate(request)
