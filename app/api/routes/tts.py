"""TTS API route — Gemini 2.5 Flash TTS for native multilingual voices."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from app.services.tts_service import tts_service
from app.core.security import rate_limit_dependency

router = APIRouter(prefix="/api", tags=["tts"])


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = "en"


@router.post("/tts", dependencies=[Depends(rate_limit_dependency)])
async def text_to_speech(request: TTSRequest):
    """Convert text to speech audio using Gemini 2.5 Flash TTS with native voice."""
    audio_bytes = await tts_service.synthesize(
        text=request.text,
        language=request.language,
    )

    if audio_bytes:
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "public, max-age=3600",
            },
        )

    return Response(status_code=204)  # No content — frontend will use fallback
