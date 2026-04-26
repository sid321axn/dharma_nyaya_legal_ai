"""Translation and language detection service."""

import re
from typing import Optional
from app.services.gemma_service import gemma_service
from app.core.logging import logger
from app.models.schemas import LANGUAGE_NAMES

# Unicode range heuristics for language detection
_LANG_PATTERNS: list[tuple[str, str]] = [
    (r'[\u0900-\u097F]', 'hi'),     # Devanagari → Hindi
    (r'[\u0980-\u09FF]', 'bn'),     # Bengali
    (r'[\u0B80-\u0BFF]', 'ta'),     # Tamil
    (r'[\u0C00-\u0C7F]', 'te'),     # Telugu
    (r'[\u0C80-\u0CFF]', 'kn'),     # Kannada
    (r'[\u0B00-\u0B7F]', 'or'),     # Odia
    (r'[\u0A80-\u0AFF]', 'gu'),     # Gujarati
    (r'[\u1C50-\u1C7F]', 'sat'),    # Ol Chiki → Santali
    (r'[\u0400-\u04FF]', 'uk'),     # Cyrillic → Ukrainian
]


class TranslationService:
    """Language detection and translation via Gemma."""

    def detect_language(self, text: str) -> str:
        """Detect language from text using Unicode heuristics."""
        for pattern, lang_code in _LANG_PATTERNS:
            if re.search(pattern, text):
                return lang_code
        return "en"

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text between languages using Gemma."""
        if source_lang == target_lang:
            return text

        source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)

        prompt = (
            f"Translate the following text from {source_name} to {target_name}. "
            "Output ONLY the translated text, nothing else.\n\n"
            f"{text}"
        )
        try:
            result = await gemma_service.generate_text(prompt, language=target_lang)
            return result.strip()
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text  # Fallback to original

    async def ensure_language(self, text: str, target_lang: str) -> str:
        """Detect source language and translate to target if needed."""
        source = self.detect_language(text)
        if source == target_lang:
            return text
        return await self.translate(text, source, target_lang)


translation_service = TranslationService()
