"""Follow-up Agent — simulated case tracking, deadlines, and recommendations."""

from datetime import datetime, timedelta
from app.models.schemas import FollowUpInfo
from app.models.database import get_case
from app.services.gemma_service import gemma_service
from app.core.logging import logger


class FollowUpAgent:
    """Track case progress, deadlines, and provide recommendations."""

    async def get_followup(self, case_id: str, language: str = "en") -> FollowUpInfo:
        """Generate follow-up information for a case."""
        case = get_case(case_id)

        if not case:
            return FollowUpInfo(
                case_id=case_id,
                next_steps=["Case not found. Please start a new consultation."],
                deadlines=[],
                recommendations=["Start a new chat session to create a case."],
                status_update="Case not found.",
            )

        prompt = (
            f"Based on this legal case, provide follow-up guidance:\n"
            f"Title: {case.get('title', 'N/A')}\n"
            f"Domain: {case.get('legal_domain', 'N/A')}\n"
            f"Description: {case.get('description', 'N/A')}\n"
            f"Status: {case.get('status', 'open')}\n\n"
            "Provide:\n"
            "1. Next steps the person should take\n"
            "2. Important deadlines to be aware of\n"
            "3. Recommendations for the best outcome"
        )

        try:
            response = await gemma_service.generate_text(prompt, language=language)
            now = datetime.utcnow()

            return FollowUpInfo(
                case_id=case_id,
                next_steps=[response[:500]],
                deadlines=[
                    {"description": "Follow up on initial filing", "date": (now + timedelta(days=7)).isoformat()},
                    {"description": "Document submission deadline", "date": (now + timedelta(days=30)).isoformat()},
                ],
                recommendations=["Keep all documents organized",
                                  "Note down all communication dates",
                                  "Consult a local lawyer if needed"],
                status_update=f"Case is currently: {case.get('status', 'open')}",
            )
        except Exception as e:
            logger.error(f"FollowUpAgent error: {e}")
            return FollowUpInfo(
                case_id=case_id,
                next_steps=["Unable to generate follow-up. Please try again."],
                deadlines=[],
                recommendations=["Please try again later."],
                status_update="Error generating follow-up.",
            )


followup_agent = FollowUpAgent()
