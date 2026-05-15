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
                            system_instruction: str = "",
                            voice_mode: bool = False) -> str:
        """Generate text using Gemma model (streaming collected to string).

        Set ``voice_mode=True`` to suppress markdown/format instructions so the
        response contains only plain spoken sentences suitable for TTS playback.
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

        if voice_mode:
            # Voice/TTS: no markdown, no formatting — system_instruction carries all rules.
            format_instruction = ""
        else:
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
    # Well-known legal sites → proper display names
    _KNOWN_SITE_NAMES: dict[str, str] = {
        "indiankanoon.org": "Indian Kanoon",
        "indiacode.nic.in": "India Code",
        "sci.gov.in": "Supreme Court of India",
        "main.sci.gov.in": "Supreme Court of India",
        "legislative.gov.in": "Ministry of Law – Legislative Dept",
        "labour.gov.in": "Ministry of Labour & Employment",
        "consumeraffairs.nic.in": "Consumer Affairs Ministry",
        "nalsa.gov.in": "NALSA – Legal Aid Services",
        "rtionline.gov.in": "RTI Online Portal",
        "rera.gov.in": "RERA Portal",
        "zakon.rada.gov.ua": "Verkhovna Rada – Ukraine Laws",
        "minjust.gov.ua": "Ministry of Justice – Ukraine",
        "court.gov.ua": "Ukrainian Courts",
        "eur-lex.europa.eu": "EUR-Lex – EU Law",
        "curia.europa.eu": "Court of Justice of the EU",
        "legislation.gov.uk": "UK Legislation",
        "gov.uk": "UK Government",
        "citizensadvice.org.uk": "Citizens Advice (UK)",
        "bailii.org": "BAILII – UK & Irish Law",
        "law.cornell.edu": "Cornell Law School",
        "uscode.house.gov": "US Code",
        "ftc.gov": "FTC – US Federal Trade Commission",
        "dol.gov": "US Dept of Labor",
        "consumerfinance.gov": "US Consumer Financial Protection",
        "justia.com": "Justia – US Law",
        "legislation.gov.au": "Australian Legislation",
        "austlii.edu.au": "AustLII – Australian Law",
        "laws-lois.justice.gc.ca": "Canada Laws – Justice.gc.ca",
        "canlii.org": "CanLII – Canadian Law",
        "legalservicesindia.com": "Legal Services India",
    }

    @staticmethod
    def _humanize_title(raw: str) -> str:
        """Convert a bare domain name to a readable display title."""
        import re as _re
        if not raw:
            return "Source"
        # Check known-names lookup first (raw may be the domain itself)
        known = GemmaService._KNOWN_SITE_NAMES.get(raw.lower().rstrip("/"))
        if known:
            return known
        # If it already looks like a proper title (has spaces), keep it
        if " " in raw or sum(1 for c in raw if c.isupper()) > 1:
            return raw
        clean = raw.split("/")[0].lower()
        # Strip multi-part gov TLDs (.nic.in, .gov.in, .gov.uk, etc.)
        clean = _re.sub(r"\.(nic|gov|org|ac|co|edu)\.(in|uk|au|nz|za)$", "", clean)
        # Strip single TLDs
        clean = _re.sub(r"\.(com|co|in|org|net|gov|edu|io|uk|au|ca|de|fr|ua|eu|info|law)$", "", clean)
        # Strip common subdomains
        clean = _re.sub(r"^(www|m|en|main)\.", "", clean)
        # Replace delimiters with spaces and title-case
        clean = _re.sub(r"[-_.]", " ", clean).strip()
        return clean.title() if clean else raw

    @staticmethod
    def format_sources_markdown(sources: list[dict]) -> str:
        """Render grounding sources as HTML badge links (no raw URLs shown)."""
        if not sources:
            return ""
        badges = "".join(
            f'<a href="{s.get("uri", "#")}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-flex;align-items:center;gap:5px;padding:5px 12px;'
            f'background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;border-radius:9999px;'
            f'font-size:12px;font-weight:500;text-decoration:none;margin:3px 3px 0 0;">'
            f'<span>\U0001f517</span>'
            f'<span>{GemmaService._humanize_title(s.get("title") or "")}</span>'
            f'</a>'
            for s in sources
        )
        return (
            f'<div style="margin-top:14px;padding-top:12px;border-top:1px solid #e5e7eb;">'
            f'<p style="font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;'
            f'letter-spacing:0.05em;margin-bottom:8px;">\U0001f517 Verified Sources</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{badges}</div>'
            f'</div>'
        )

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
