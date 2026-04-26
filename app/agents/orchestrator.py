"""Orchestrator Agent — central brain that routes queries to appropriate agents."""

import json
import re
import asyncio
from typing import AsyncGenerator, Callable, Optional

from app.agents.intake_agent import intake_agent
from app.agents.rights_agent import rights_agent
from app.agents.action_agent import action_agent
from app.agents.followup_agent import followup_agent
from app.services.gemma_service import gemma_service, GemmaService
from app.services.translation_service import translation_service
from app.models.schemas import ChatResponse, IntakeResult
from app.models.database import (
    get_or_create_session, add_message, get_history, create_case
)
from app.core.config import get_settings
from app.core.logging import logger

_AGENT_FUNCTIONS = [
    {"name": "rights_analyzer", "description": "Analyze legal rights and provide explanations"},
    {"name": "action_generator", "description": "Generate legal documents (complaints, notices, RTI)"},
    {"name": "followup_tracker", "description": "Track case progress and deadlines"},
    {"name": "general_chat", "description": "General legal Q&A and guidance"},
]

# Human-friendly agent display names
_AGENT_DISPLAY = {
    "rights_analyzer": "Rights Advisor",
    "action_generator": "Document Writer",
    "followup_tracker": "Case Tracker",
    "general_chat": "Legal Guide",
}


class Orchestrator:
    """Central orchestrator that routes user queries to the right agents."""

    async def process_message(self, message: str, language: str = "en",
                              session_id: str | None = None,
                              mode: str | None = None) -> ChatResponse:
        """Process a user message through the multi-agent pipeline (non-streaming)."""
        session_id = get_or_create_session(session_id)
        add_message(session_id, "user", message)

        intake: IntakeResult = await intake_agent.process(message, language)
        effective_lang = intake.detected_language or language

        # Voice mode bypasses routing — always use a concise general_chat reply
        # so the answer is short, conversational, and TTS-friendly.
        if mode == "voice":
            agent_name = "general_chat"
            route = {"agent": agent_name, "parameters": {}}
        else:
            route = await self._route(message)
            agent_name = route.get("agent", "general_chat")

        try:
            reply, agent_name = await self._execute_agent(
                agent_name, route, message, intake, effective_lang, mode=mode,
            )
        except Exception as e:
            logger.error(f"Orchestrator agent execution error: {e}")
            reply = "I apologize, but I encountered an issue processing your request. Please try again."
            agent_name = "error"

        if effective_lang != "en" and effective_lang != language:
            reply = await translation_service.ensure_language(reply, effective_lang)

        add_message(session_id, "assistant", reply)
        self._maybe_create_case(intake, message, effective_lang)

        return ChatResponse(
            reply=reply,
            language=effective_lang,
            agent_used=agent_name,
            session_id=session_id,
            metadata={"intake": intake.model_dump(), "domain": intake.legal_domain},
        )

    async def process_message_stream(self, message: str, language: str = "en",
                                     session_id: str | None = None,
                                     mode: str | None = None) -> AsyncGenerator[dict, None]:
        """Process a user message and yield step-by-step SSE events."""
        session_id = get_or_create_session(session_id)
        add_message(session_id, "user", message)

        # ── Step 1: Reading your message ─────────────────────────────────
        yield {"type": "step", "step": "reading", "status": "active", "agent": "Orchestrator"}
        await asyncio.sleep(0)  # yield control so SSE flushes
        yield {"type": "step", "step": "reading", "status": "done", "agent": "Orchestrator"}

        # ── Step 2: Detecting language & understanding context ───────────
        yield {"type": "step", "step": "detecting", "status": "active", "agent": "Intake Agent"}
        intake: IntakeResult = await intake_agent.process(message, language)
        effective_lang = intake.detected_language or language
        yield {
            "type": "step", "step": "detecting", "status": "done", "agent": "Intake Agent",
            "detail": {"language": effective_lang, "domain": intake.legal_domain,
                        "jurisdiction": intake.jurisdiction},
        }

        # ── Step 3: Choosing the right expert ────────────────────────────
        yield {"type": "step", "step": "routing", "status": "active", "agent": "Orchestrator"}
        if mode == "voice":
            # Voice mode — skip routing, always go to a concise general_chat reply.
            agent_name = "general_chat"
            route = {"agent": agent_name, "parameters": {}}
        else:
            route = await self._route(message)
            agent_name = route.get("agent", "general_chat")
        display = _AGENT_DISPLAY.get(agent_name, agent_name)
        yield {
            "type": "step", "step": "routing", "status": "done", "agent": "Orchestrator",
            "detail": {"chosen_agent": display},
        }

        # ── Step 4: Expert is working ────────────────────────────────────
        yield {"type": "step", "step": "thinking", "status": "active", "agent": display}
        try:
            reply, agent_name = await self._execute_agent(
                agent_name, route, message, intake, effective_lang, mode=mode,
            )
        except Exception as e:
            logger.error(f"Orchestrator agent execution error: {e}")
            reply = "I apologize, but I encountered an issue processing your request. Please try again."
            agent_name = "error"
        yield {"type": "step", "step": "thinking", "status": "done", "agent": display}

        # ── Step 5: Translating if needed ────────────────────────────────
        if effective_lang != "en" and effective_lang != language:
            yield {"type": "step", "step": "translating", "status": "active", "agent": "Translator"}
            reply = await translation_service.ensure_language(reply, effective_lang)
            yield {"type": "step", "step": "translating", "status": "done", "agent": "Translator"}

        # ── Step 6: Preparing your answer ────────────────────────────────
        yield {"type": "step", "step": "preparing", "status": "active", "agent": display}
        add_message(session_id, "assistant", reply)
        self._maybe_create_case(intake, message, effective_lang)
        yield {"type": "step", "step": "preparing", "status": "done", "agent": display}

        # ── Final: Send the complete response ────────────────────────────
        tts_text = self._build_tts_text(reply, effective_lang)
        yield {
            "type": "done",
            "reply": reply,
            "tts_text": tts_text,
            "language": effective_lang,
            "agent_used": agent_name,
            "session_id": session_id,
            "metadata": {"intake": intake.model_dump(), "domain": intake.legal_domain},
        }

    async def _execute_agent(self, agent_name: str, route: dict, message: str,
                             intake: IntakeResult, lang: str,
                             mode: str | None = None) -> tuple[str, str]:
        """Execute the selected agent and return (reply, agent_name)."""
        if agent_name == "rights_analyzer":
            result = await rights_agent.analyze(
                message, legal_domain=intake.legal_domain, language=lang
            )
            reply = result.legal_explanation

        elif agent_name == "action_generator":
            from app.models.schemas import ActionRequest, ActionType
            action_type = route.get("parameters", {}).get("action_type", "complaint_letter")
            try:
                at = ActionType(action_type)
            except ValueError:
                at = ActionType.COMPLAINT_LETTER
            req = ActionRequest(action_type=at, context=message, language=lang)
            result = await action_agent.generate(req)
            reply = result.content

        elif agent_name == "followup_tracker":
            case_id = route.get("parameters", {}).get("case_id", "")
            result = await followup_agent.get_followup(case_id, language=lang)
            reply = result.status_update + "\n\n" + "\n".join(result.next_steps)

        else:
            settings = get_settings()
            general_system = (
                "You are DHARMA-NYAYA, an AI legal assistant. "
                "Help citizens understand their legal rights in simple terms. "
                "Be empathetic, clear, and actionable. "
                "Use ### headings with emojis, **bold** key terms, bullet points, and --- separators. "
                "End with a warm invitation asking the user to ask follow-up questions."
            )
            if mode == "voice":
                # Voice mode: short, conversational, no markdown chrome, no source block.
                # The reply is read out by TTS, so plain spoken English/Hindi works best.
                voice_system = (
                    "You are DHARMA-NYAYA, an AI legal assistant speaking to a citizen "
                    "over a LIVE VOICE call. Reply in a warm, conversational tone — like "
                    "a knowledgeable friend, not a textbook.\n\n"
                    "STRICT VOICE RULES:\n"
                    "- Keep the reply SHORT: 2 to 4 sentences, max ~80 words.\n"
                    "- Address the user's specific question directly. No long preambles.\n"
                    "- NO markdown, NO headings, NO bullet points, NO emojis, NO links, "
                    "NO source citations — just plain spoken sentences.\n"
                    "- Mention at most ONE Act or section, only if essential.\n"
                    "- ALWAYS end with a friendly question inviting more details, "
                    "e.g. 'Would you like to know more?' or 'Shall I explain how to file it?' "
                    "— phrased naturally in the user's language."
                )
                reply = await gemma_service.generate_text(
                    message, language=lang, system_instruction=voice_system,
                )
            elif settings.USE_GOOGLE_SEARCH_GROUNDING:
                grounded = await gemma_service.generate_text_with_sources(
                    message, language=lang, system_instruction=general_system,
                )
                reply = grounded["text"] + GemmaService.format_grounding_block(
                    grounded.get("sources", []),
                )
            else:
                reply = await gemma_service.generate_text(
                    message, language=lang, system_instruction=general_system,
                )
        return reply, agent_name

    def _maybe_create_case(self, intake: IntakeResult, message: str, lang: str) -> None:
        if intake.legal_domain != "other":
            create_case(
                title=intake.summary or message[:100],
                description=message,
                language=lang,
                legal_domain=intake.legal_domain,
                jurisdiction=intake.jurisdiction,
            )

    async def _route(self, message: str) -> dict:
        """Route the message to the appropriate agent using Gemma function calling."""
        try:
            return await gemma_service.function_call(message, _AGENT_FUNCTIONS)
        except Exception as e:
            logger.warning(f"Routing fallback to general_chat: {e}")
            return {"agent": "general_chat", "parameters": {}}

    # ── TTS text builder ─────────────────────────────────────────────────

    _TTS_CLOSING = {
        "en": "For more details, please read below. If you need help understanding anything, I am here for you.",
        "hi": "अधिक जानकारी के लिए कृपया नीचे पढ़ें। अगर कोई बात समझ न आए तो मैं आपकी मदद के लिए हूँ।",
        "bn": "আরও বিস্তারিত জানতে নিচে পড়ুন। কিছু বুঝতে না পারলে আমি আপনাকে সাহায্য করতে এখানে আছি।",
        "ta": "மேலும் விவரங்களுக்கு கீழே படிக்கவும். புரியாத விஷயம் இருந்தால் நான் உங்களுக்கு உதவ இங்கே இருக்கிறேன்.",
        "te": "మరిన్ని వివరాలకు దయచేసి క్రింద చదవండి. ఏదైనా అర్థం కాకపోతే నేను మీకు సహాయం చేయడానికి ఇక్కడ ఉన్నాను.",
        "kn": "ಹೆಚ್ಚಿನ ವಿವರಗಳಿಗಾಗಿ ಕೆಳಗೆ ಓದಿ. ಏನಾದರೂ ಅರ್ಥವಾಗದಿದ್ದರೆ ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಇಲ್ಲಿದ್ದೇನೆ.",
        "uk": "Для детальнішої інформації прочитайте нижче. Якщо щось незрозуміло, я тут щоб допомогти.",
        "sat": "ᱟᱨ ᱡᱟᱱᱟᱣ ᱞᱟᱹᱜᱤᱫ ᱛᱚᱞᱮ ᱯᱟᱲᱦᱟᱣ ᱢᱮ। ᱡᱩᱫᱤ ᱠᱚᱱᱟᱜ ᱠᱟᱛᱷᱟ ᱵᱩᱡᱷᱟᱹᱣ ᱵᱟᱝ ᱦᱩᱭᱩᱜ ᱠᱟᱱᱟ ᱛᱚᱵᱮ ᱟᱺᱡ ᱟᱢᱟᱜ ᱜᱚᱲᱚ ᱞᱟᱹᱜᱤᱫ ᱱᱚᱣᱟ ᱨᱮ ᱢᱮᱱᱟᱺ ᱠᱟᱱᱟ।",
    }

    @staticmethod
    def _build_tts_text(reply: str, language: str) -> str:
        """Extract first 2 meaningful paragraphs from reply for TTS.
        Strips markdown, appends a closing invitation line."""
        # Strip markdown formatting
        clean = re.sub(r'#{1,6}\s*', '', reply)
        clean = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', clean)
        clean = clean.replace('`', '').replace('---', '')

        # Split into paragraphs (non-empty lines separated by blank lines)
        paragraphs = []
        for block in re.split(r'\n\s*\n', clean):
            text = block.strip()
            # Skip very short lines (emoji headers, bullet labels)
            if text and len(text) > 30:
                paragraphs.append(text)

        # Take first 2 paragraphs
        spoken = ' '.join(paragraphs[:2]) if paragraphs else clean[:300]

        # Cap at ~500 chars for fast TTS generation
        if len(spoken) > 500:
            # Cut at last sentence boundary
            cut = spoken[:500]
            last_period = max(cut.rfind('।'), cut.rfind('.'), cut.rfind('|'))
            if last_period > 200:
                spoken = cut[:last_period + 1]
            else:
                spoken = cut + '...'

        closing = Orchestrator._TTS_CLOSING.get(language, Orchestrator._TTS_CLOSING['en'])
        return f"{spoken} {closing}"


orchestrator = Orchestrator()
