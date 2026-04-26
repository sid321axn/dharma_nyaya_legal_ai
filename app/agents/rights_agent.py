"""Rights Analyzer Agent — uses RAG to provide legal analysis with section references."""

from app.services.gemma_service import gemma_service, GemmaService
from app.services.rag_service import rag_service
from app.models.schemas import RightsAnalysis, LANGUAGE_NAMES
from app.core.config import get_settings
from app.core.logging import logger


class RightsAgent:
    """Analyze legal rights with RAG-augmented context."""

    async def analyze(self, query: str, legal_domain: str = "",
                      language: str = "en") -> RightsAnalysis:
        """Provide legal analysis with references."""
        lang_name = LANGUAGE_NAMES.get(language, language)
        # Retrieve relevant legal context
        rag_results = await rag_service.search(query, domain=legal_domain or None)
        context = rag_service.format_context(rag_results)

        prompt = (
            f"You are a legal rights analyst. Respond ENTIRELY in {lang_name}.\n"
            "Based on the legal context and user query below, provide:\n"
            "1. ⚖️ A detailed legal explanation with section references\n"
            "2. 📋 Relevant section references from applicable laws\n"
            "3. 💡 A simplified explanation that a common citizen can understand\n"
            "4. ✅ Practical step-by-step recommendations\n\n"
            "Use ### headings with emojis, **bold** key terms, bullet points, --- separators.\n"
            f"Translate ALL content including law names and section titles into {lang_name}.\n\n"
            f"Legal Context:\n{context}\n\n"
            f"User Query: {query}\n\n"
            "Provide a comprehensive but clear response. "
            "End with a warm invitation to ask follow-up questions."
        )

        try:
            settings = get_settings()
            if settings.USE_GOOGLE_SEARCH_GROUNDING:
                grounded = await gemma_service.generate_text_with_sources(
                    prompt, language=language,
                    system_instruction="You are a legal rights expert. Be thorough but accessible.",
                )
                response = grounded["text"] + GemmaService.format_grounding_block(
                    grounded.get("sources", []),
                )
            else:
                response = await gemma_service.generate_text(prompt, language=language,
                    system_instruction="You are a legal rights expert. Be thorough but accessible.")

            sections = [s["sections"] for s in rag_results]
            flat_sections = [sec for sublist in sections for sec in sublist]

            return RightsAnalysis(
                legal_explanation=response,
                section_references=flat_sections,
                simplified_explanation=response,  # In production, generate a separate simplified version
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
