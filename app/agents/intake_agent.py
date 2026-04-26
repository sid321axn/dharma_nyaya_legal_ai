"""Intake Agent — detects language, legal domain, jurisdiction, and extracts structured info."""

import json
from app.services.gemma_service import gemma_service
from app.services.translation_service import translation_service
from app.models.schemas import IntakeResult
from app.core.logging import logger


class IntakeAgent:
    """Analyze user input and extract structured metadata."""

    async def process(self, message: str, language: str = "en") -> IntakeResult:
        """Detect language, legal domain, jurisdiction from user message."""
        detected_lang = translation_service.detect_language(message)
        if detected_lang != "en":
            language = detected_lang

        prompt = (
            "Analyze the following user query about a legal issue. "
            "Return a JSON object with these keys:\n"
            '- "legal_domain": one of [labor, consumer, property, family, criminal, rti, civil, other]\n'
            '- "jurisdiction": detected location/state/country or "unknown"\n'
            '- "urgency": one of [low, normal, high, critical]\n'
            '- "entities": a dict of extracted entities (names, dates, amounts, etc.)\n'
            '- "summary": a one-line summary of the issue\n\n'
            "Respond ONLY with valid JSON.\n\n"
            f"User query: {message}"
        )

        try:
            response = await gemma_service.generate_text(prompt, language="en",
                system_instruction="You are a legal intake analyst. Output only JSON.")
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(response)
            return IntakeResult(
                detected_language=language,
                legal_domain=data.get("legal_domain", "other"),
                jurisdiction=data.get("jurisdiction", "unknown"),
                urgency=data.get("urgency", "normal"),
                entities=data.get("entities", {}),
                summary=data.get("summary", ""),
            )
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"IntakeAgent parse error: {e}")
            return IntakeResult(
                detected_language=language,
                legal_domain="other",
                jurisdiction="unknown",
                summary=message[:200],
            )


intake_agent = IntakeAgent()
