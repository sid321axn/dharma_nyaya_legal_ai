"""Chat API route — main conversational endpoint with SSE streaming."""

import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse
from app.agents.orchestrator import orchestrator
from app.core.security import rate_limit_dependency, sanitize_input

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message (non-streaming fallback)."""
    clean_message = sanitize_input(request.message)
    return await orchestrator.process_message(
        message=clean_message,
        language=request.language,
        session_id=request.session_id,
        mode=request.mode,
    )


@router.post("/chat/stream", dependencies=[Depends(rate_limit_dependency)])
async def chat_stream(request: ChatRequest):
    """Stream agent steps as Server-Sent Events so the UI shows real-time progress."""
    clean_message = sanitize_input(request.message)

    async def event_generator():
        async for event in orchestrator.process_message_stream(
            message=clean_message,
            language=request.language,
            session_id=request.session_id,
            mode=request.mode,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
