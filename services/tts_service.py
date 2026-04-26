"""Gemini TTS service — uses gemini-2.5-flash-tts for native multilingual speech."""

import asyncio
import io
import wave
from typing import Optional

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.logging import logger


# Voice selection per language — Puck (male, upbeat) for Indian locales, Charon (male, informative) for English
VOICE_MAP = {
    "hi": "Puck",
    "bn": "Puck",
    "ta": "Puck",
    "te": "Puck",
    "kn": "Puck",
    "mr": "Puck",
    "gu": "Puck",
    "sat": "Puck",
    "en": "Charon",
    "uk": "Charon",
}

TTS_MODEL = "gemini-2.5-flash-preview-tts"


class TTSService:
    """Gemini 2.5 Flash TTS wrapper — generates native speech from text."""

    def __init__(self):
        self._api_key = get_settings().GEMINI_API_KEY
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def synthesize(self, text: str, language: str = "en") -> Optional[bytes]:
        """
        Convert text to speech using Gemini 2.5 Flash TTS.
        Returns WAV audio bytes, or None on failure.
        """
        if not text or not self._api_key:
            return None

        # Clean text — strip markdown symbols
        clean = (
            text
            .replace("**", "")
            .replace("*", "")
            .replace("#", "")
            .replace("`", "")
            .replace("---", "")
            .strip()
        )
        if not clean:
            return None

        voice_name = VOICE_MAP.get(language, "Kore")

        try:
            # Gemini TTS is sync — run in thread pool to avoid blocking
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=TTS_MODEL,
                contents=clean,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                ),
            )

            # Extract audio data from response
            if (
                response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
            ):
                part = response.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    audio_data = part.inline_data.data
                    mime = part.inline_data.mime_type or ""
                    logger.info(f"TTS generated {len(audio_data)} bytes, mime={mime}")

                    # Gemini returns raw PCM — wrap in WAV container
                    if "wav" not in mime.lower() and "pcm" in mime.lower() or "L16" in mime:
                        audio_data = self._pcm_to_wav(
                            audio_data,
                            sample_rate=24000,
                            channels=1,
                            sample_width=2,
                        )
                    return audio_data

            logger.warning("TTS response had no audio content")
            return None

        except Exception as e:
            logger.error(f"Gemini TTS error: {e}")
            return None

    @staticmethod
    def _pcm_to_wav(
        pcm_data: bytes,
        sample_rate: int = 24000,
        channels: int = 1,
        sample_width: int = 2,
    ) -> bytes:
        """Wrap raw PCM bytes in a WAV header."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
        return buf.getvalue()


tts_service = TTSService()
