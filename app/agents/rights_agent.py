"""Rights Analyzer Agent — uses RAG to provide legal analysis with section references."""

from app.services.gemma_service import gemma_service, GemmaService
from app.services.rag_service import rag_service
from app.models.schemas import RightsAnalysis, LANGUAGE_NAMES
from app.core.config import get_settings
from app.core.logging import logger

# Jurisdictions that are clearly NOT India — skip Indian RAG context for these
_NON_INDIA_KEYWORDS = [
    "london", "england", "uk", "united kingdom", "britain", "scotland", "wales",
    "usa", "us ", "united states", "america", "california", "new york", "texas",
    "canada", "ontario", "toronto", "australia", "sydney", "melbourne",
    "ukraine", "germany", "france", "italy", "spain", "netherlands", "eu ",
    "europe", "european union", "dubai", "uae", "singapore", "malaysia",
    "new zealand", "south africa", "pakistan", "bangladesh", "kenya",
]

_JURISDICTION_SOURCES = {
    "uk": "UK (legislation.gov.uk, gov.uk, citizensadvice.org.uk, bailii.org)",
    "usa": "USA (law.cornell.edu, uscode.house.gov, ftc.gov, dol.gov, justia.com)",
    "ukraine": "Ukraine (zakon.rada.gov.ua, minjust.gov.ua, court.gov.ua)",
    "eu": "EU (eur-lex.europa.eu, curia.europa.eu)",
    "australia": "Australia (legislation.gov.au, austlii.edu.au)",
    "canada": "Canada (laws-lois.justice.gc.ca, canlii.org)",
    "india": "India (indiankanoon.org, indiacode.nic.in, sci.gov.in, legislative.gov.in, nalsa.gov.in)",
}


def _detect_jurisdiction(message: str, jurisdiction_hint: str) -> tuple[str, str]:
    """
    Returns (jurisdiction_key, human_name).
    jurisdiction_key: 'uk' | 'usa' | 'ukraine' | 'eu' | 'australia' | 'canada' | 'india' | 'other:<name>'
    """
    combined = (message + " " + jurisdiction_hint).lower()

    if any(k in combined for k in ["london", "england", "uk", "united kingdom", "britain",
                                     "scotland", "wales", "england and wales"]):
        return "uk", "United Kingdom"
    if any(k in combined for k in ["ukraine", "ukrainian", "kyiv", "kiev"]):
        return "ukraine", "Ukraine"
    if any(k in combined for k in ["usa", "united states", "america", "california",
                                     "new york", "texas", "florida", "illinois",
                                     "federal law us", "us law"]):
        return "usa", "United States"
    if any(k in combined for k in ["australia", "sydney", "melbourne", "queensland"]):
        return "australia", "Australia"
    if any(k in combined for k in ["canada", "ontario", "toronto", "british columbia",
                                     "alberta", "quebec"]):
        return "canada", "Canada"
    if any(k in combined for k in ["germany", "german", "deutschland"]):
        return "other:germany", "Germany"
    if any(k in combined for k in ["france", "french", "paris"]):
        return "other:france", "France"
    if any(k in combined for k in ["eu ", "european union", "gdpr", "europe"]):
        return "eu", "European Union"
    if any(k in combined for k in ["dubai", "uae", "abu dhabi", "emirates"]):
        return "other:uae", "United Arab Emirates"
    if any(k in combined for k in ["singapore"]):
        return "other:singapore", "Singapore"
    # Default to India
    return "india", "India"


class RightsAgent:
    """Analyze legal rights with RAG-augmented context."""

    async def analyze(self, query: str, legal_domain: str = "",
                      language: str = "en",
                      jurisdiction: str = "") -> RightsAnalysis:
        """Provide legal analysis with references."""
        lang_name = LANGUAGE_NAMES.get(language, language)

        jur_key, jur_name = _detect_jurisdiction(query, jurisdiction)
        is_india = jur_key == "india"
        source_hint = _JURISDICTION_SOURCES.get(jur_key) or f"{jur_name} (official government and court websites)"

        # Only use Indian RAG context when the query is actually about India
        if is_india:
            rag_results = await rag_service.search(query, domain=legal_domain or None)
            context = rag_service.format_context(rag_results)
            rag_instruction = f"Legal Context (Indian law database):\n{context}\n\n" if context else ""
        else:
            rag_results = []
            rag_instruction = ""

        jurisdiction_block = (
            f"JURISDICTION: {jur_name}\n"
            f"CRITICAL RULE: This question is about {jur_name} law. "
            f"Answer EXCLUSIVELY using {jur_name} law, legislation, and court precedents. "
            + ("Do NOT reference Indian law, IPC, CrPC, Indian Contract Act, or any Indian legislation. "
               if not is_india else "")
            + f"Cite only from: {source_hint}\n\n"
        )

        clarification_block = (
            "CLARIFICATION RULE: Before giving a full response, check if critical information is missing.\n"
            "- If the country/jurisdiction is NOT clearly stated → ask: 'Could you tell me which country or state you are in, so I can give you the exact law that applies?'\n"
            "- If the nature of the problem is vague or could mean multiple things → ask ONE targeted question to clarify.\n"
            "- If the user's role (tenant/landlord, employee/employer, buyer/seller, etc.) is unclear → ask which side they are on.\n"
            "Ask ONLY ONE clarifying question if needed, and wait for the answer before giving legal advice.\n"
            "If enough information IS available → give the full response without asking.\n\n"
        )

        prompt = (
            f"You are a legal rights analyst. Respond ENTIRELY in {lang_name}.\n"
            + jurisdiction_block
            + clarification_block
            + "Based on the query below, provide:\n"
            "1. ⚖️ A detailed legal explanation with section references from the CORRECT jurisdiction\n"
            "2. 📋 Relevant section references from applicable laws\n"
            "3. 💡 A simplified explanation that a common citizen can understand\n"
            "4. ✅ Practical step-by-step recommendations\n"
            "5. 🔗 End with 2-4 authentic clickable references ONLY from: " + source_hint + "\n\n"
            "Use ### headings with emojis, **bold** key terms, bullet points, --- separators.\n"
            f"Translate ALL content including law names and section titles into {lang_name}.\n\n"
            + rag_instruction
            + f"User Query: {query}\n\n"
            "Provide a comprehensive but clear response. "
            "End with a warm invitation to ask follow-up questions."
        )

        try:
            settings = get_settings()
            system_instr = (
                f"You are a legal rights expert specializing in {jur_name} law. "
                "Be thorough but accessible. "
                + ("Never mention Indian law for non-Indian jurisdictions. " if not is_india else "")
            )
            if settings.USE_GOOGLE_SEARCH_GROUNDING:
                grounded = await gemma_service.generate_text_with_sources(
                    prompt, language=language,
                    system_instruction=system_instr,
                )
                response = grounded["text"] + GemmaService.format_grounding_block(
                    grounded.get("sources", []),
                )
            else:
                response = await gemma_service.generate_text(
                    prompt, language=language,
                    system_instruction=system_instr,
                )

            sections = [s["sections"] for s in rag_results]
            flat_sections = [sec for sublist in sections for sec in sublist]

            return RightsAnalysis(
                legal_explanation=response,
                section_references=flat_sections,
                simplified_explanation=response,
                recommendations=["Consult a local lawyer for case-specific advice",
                                  "Keep all relevant documents safe",
                                  "Note down important dates and deadlines"],
                language=language,
            )
        except Exception as e:
            logger.error(f"RightsAgent error: {e}")
            return RightsAnalysis(
                legal_explanation="Unable to analyze at this time. Please try again.",
                section_references=[],
                simplified_explanation="Our system encountered an issue. Please try again.",
                recommendations=["Please try again later or consult a local legal aid center."],
                language=language,
            )


rights_agent = RightsAgent()
