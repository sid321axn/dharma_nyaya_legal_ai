"""Gemma API service — wraps google-genai client for text, multimodal, and function calling.
Reuses patterns from gemma_use.py reference file.
"""

import os
import json
from typing import Optional, Any
from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.logging import logger


class GemmaService:
    """Async wrapper around Gemma 4 31B API."""

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMMA_MODEL
        self._thinking_level = settings.GEMMA_THINKING_LEVEL
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        """Lazy-init the genai client."""
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def generate_text(self, prompt: str, language: str = "en",
                            system_instruction: str = "") -> str:
        """Generate text using Gemma model (streaming collected to string)."""
        from app.models.schemas import LANGUAGE_NAMES
        lang_name = LANGUAGE_NAMES.get(language, language)

        if language != "en":
            lang_instruction = (
                f"CRITICAL LANGUAGE RULE: You MUST respond ENTIRELY in {lang_name} (language code: '{language}'). "
                f"Do NOT use English or any other language at all — not for headings, not for section names, "
                f"not for labels, not for legal citations. Translate EVERYTHING including legal act names, "
                f"section references, and headings into {lang_name}. "
            )
        else:
            lang_instruction = ""

        format_instruction = (
            "FORMAT RULES: "
            "- Use emojis at the start of each section heading (e.g. ⚖️, 📋, 🛡️, 💡, 📌, ✅, ⚠️, 🔍). "
            "- Use ### for main section headings and **bold** for key terms. "
            "- Use bullet points and numbered lists for clarity. "
            "- Use --- horizontal rules to separate sections. "
            "- Keep language simple, empathetic, and citizen-friendly. "
            "- At the very end of your response, add a warm line inviting the user to ask "
            "follow-up questions if they need more help or don't understand something. "
        )

        full_system = (
            "You are DHARMA-NYAYA, an AI legal assistant that helps citizens understand "
            "their legal rights and generates legal documents. "
            f"{lang_instruction}{format_instruction}{system_instruction}"
        )

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]

        config = types.GenerateContentConfig(
            system_instruction=full_system,
            thinking_config=types.ThinkingConfig(
                thinking_level=self._thinking_level,
            ),
        )

        try:
            result_parts: list[str] = []
            for chunk in self.client.models.generate_content_stream(
                model=self._model,
                contents=contents,
                config=config,
            ):
                if text := chunk.text:
                    result_parts.append(text)
            return "".join(result_parts)
        except Exception as e:
            logger.error(f"Gemma generate_text error: {e}")
            raise

    async def generate_text_with_sources(self, prompt: str, language: str = "en",
                                         system_instruction: str = "") -> dict:
        """Generate the answer with Gemma 4 + Google Search grounding in ONE call.

        Gemma 4 31B fully supports the ``googleSearch`` tool (note camelCase — the
        snake_case alias ``google_search`` is silently no-op'd by the SDK). The model
        runs real Google Search queries during generation, and the resulting source
        URLs come back in ``candidates[*].grounding_metadata.grounding_chunks``.

        Returns ``{"text": str, "sources": [{"title", "uri"}]}``.
        Falls back to non-grounded text on any error so the answer is never lost.
        """
        from app.models.schemas import LANGUAGE_NAMES
        lang_name = LANGUAGE_NAMES.get(language, language)

        if language != "en":
            lang_instruction = (
                f"CRITICAL LANGUAGE RULE: You MUST respond ENTIRELY in {lang_name} (language code: '{language}'). "
                f"Do NOT use English or any other language at all — not for headings, not for section names, "
                f"not for labels, not for legal citations. Translate EVERYTHING including legal act names, "
                f"section references, and headings into {lang_name}. "
            )
        else:
            lang_instruction = ""

        format_instruction = (
            "FORMAT RULES: "
            "- Use emojis at the start of each section heading (e.g. ⚖️, 📋, 🛡️, 💡, 📌, ✅, ⚠️, 🔍). "
            "- Use ### for main section headings and **bold** for key terms. "
            "- Use bullet points and numbered lists for clarity. "
            "- Use --- horizontal rules to separate sections. "
            "- Keep language simple, empathetic, and citizen-friendly. "
            "- At the very end of your response, add a warm line inviting the user to ask "
            "follow-up questions if they need more help or don't understand something. "
        )

        grounding_instruction = (
            "GROUNDING RULES: You have a Google Search tool. Before quoting any "
            "Indian Act, section number, judgment name, or citation, RUN A GOOGLE "
            "SEARCH to confirm the citation is accurate and up to date. Prefer "
            "official sources: indiacode.nic.in, indiankanoon.org, sci.gov.in, "
            "and government portals. Do not invent URLs or citations. "
        )

        full_system = (
            "You are DHARMA-NYAYA, an AI legal assistant that helps citizens understand "
            "their legal rights and generates legal documents. "
            f"{lang_instruction}{format_instruction}{grounding_instruction}{system_instruction}"
        )

        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
        ]

        # NOTE: `googleSearch` (camelCase) is required — `google_search` (snake_case)
        # is accepted by the SDK but silently ignored by Gemma. See _probe_grounding.py.
        config = types.GenerateContentConfig(
            system_instruction=full_system,
            thinking_config=types.ThinkingConfig(thinking_level=self._thinking_level),
            tools=[types.Tool(googleSearch=types.GoogleSearch())],
        )

        try:
            result_parts: list[str] = []
            sources: list[dict] = []
            seen_uris: set[str] = set()

            for chunk in self.client.models.generate_content_stream(
                model=self._model,
                contents=contents,
                config=config,
            ):
                if text := chunk.text:
                    result_parts.append(text)
                cands = getattr(chunk, "candidates", None) or []
                if cands:
                    gm = getattr(cands[0], "grounding_metadata", None)
                    if gm is not None:
                        for s in self._extract_sources(gm):
                            if s["uri"] not in seen_uris:
                                seen_uris.add(s["uri"])
                                sources.append(s)

            return {"text": "".join(result_parts), "sources": sources}
        except Exception as e:
            logger.warning(
                f"Gemma grounded generation failed; falling back to plain text: {e}"
            )
            text = await self.generate_text(prompt, language=language,
                                            system_instruction=system_instruction)
            return {"text": text, "sources": []}

    @staticmethod
    def _extract_sources(grounding_md: Any) -> list[dict]:
        """Convert grounding_metadata.grounding_chunks into a JSON-friendly list.

        Output shape: ``[{"title": str, "uri": str}, ...]`` (deduplicated by URI).
        """
        if grounding_md is None:
            return []
        chunks = getattr(grounding_md, "grounding_chunks", None) or []
        out: list[dict] = []
        seen_uris: set[str] = set()
        for c in chunks:
            web = getattr(c, "web", None)
            if not web:
                continue
            uri = getattr(web, "uri", "") or ""
            if not uri or uri in seen_uris:
                continue
            seen_uris.add(uri)
            title = getattr(web, "title", "") or uri
            out.append({"title": title, "uri": uri})
        return out

    @staticmethod
    def format_sources_markdown(sources: list[dict]) -> str:
        """Render a list of sources as a Markdown 'Sources' section."""
        if not sources:
            return ""
        lines = ["", "---", "", "### 🔗 Sources (Google Search Grounded)", ""]
        for i, s in enumerate(sources, 1):
            lines.append(f"{i}. [{s.get('title') or s.get('uri')}]({s.get('uri')})")
        return "\n".join(lines)

    @staticmethod
    def format_grounding_block(sources: list[dict]) -> str:
        """Convenience alias kept for back-compat with existing call sites."""
        return GemmaService.format_sources_markdown(sources)

    async def analyze_document(self, file_path: str, prompt: str = "",
                               language: str = "en") -> str:
        """Analyze an uploaded file (image/PDF) using Gemma multimodal API."""
        lang_note = f" Respond in the language with code '{language}'." if language != "en" else ""
        analysis_prompt = prompt or (
            "Analyze this document thoroughly. Provide: "
            "1) A clear summary, "
            "2) Any legal risks or concerns, "
            "3) Key clauses or important sections, "
            "4) Practical advice for the user. "
            f"Format your response as JSON with keys: summary, risks, key_clauses, advice.{lang_note}"
        )

        try:
            uploaded_file = self.client.files.upload(file=file_path)
            response = self.client.models.generate_content(
                model=self._model,
                contents=[uploaded_file, analysis_prompt],
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemma analyze_document error: {e}")
            raise

    async def function_call(self, prompt: str, functions: list[dict],
                            language: str = "en") -> dict:
        """Use Gemma for structured function calling / routing."""
        system_instruction = (
            "You are a routing agent. Based on the user query, decide which function/agent to call. "
            "Return a JSON object with keys: 'agent' (which agent to route to) and 'parameters' (dict). "
            f"Available agents: {json.dumps([f['name'] for f in functions])}. "
            "Respond ONLY with valid JSON, no explanation."
        )

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )

        try:
            response = self.client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
            text = response.text or "{}"
            # Extract JSON from response
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Gemma function_call returned non-JSON, defaulting to intake")
            return {"agent": "intake", "parameters": {}}
        except Exception as e:
            logger.error(f"Gemma function_call error: {e}")
            raise


# Singleton
gemma_service = GemmaService()
