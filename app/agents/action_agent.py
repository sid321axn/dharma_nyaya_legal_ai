"""Action Agent — generates legal documents like complaint letters, notices, forms."""

from app.services.gemma_service import gemma_service
from app.models.schemas import ActionRequest, ActionResponse
from app.core.logging import logger

_ACTION_TEMPLATES: dict[str, str] = {
    "complaint_letter": (
        "Generate a formal complaint letter for the following situation. "
        "Include: sender details placeholder, recipient details placeholder, "
        "date, subject line, body with facts, legal basis, and relief sought. "
        "Make it professional and legally sound."
    ),
    "legal_notice": (
        "Draft a legal notice for the following situation. "
        "Include: advocate details placeholder, client details, opposite party details, "
        "facts of the case, legal provisions violated, demand/relief, "
        "and timeline for compliance. Use formal legal language."
    ),
    "application_form": (
        "Generate a filled application form template for the following situation. "
        "Include all necessary fields with placeholder values. "
        "Make it ready for the user to fill in their actual details."
    ),
    "rti_application": (
        "Draft a Right to Information (RTI) application. "
        "Include: applicant details placeholder, PIO address placeholder, "
        "specific questions to ask, fee details (₹10 postal order), "
        "and proper format as per RTI Act 2005, Section 6."
    ),
}


class ActionAgent:
    """Generate legal documents and actions."""

    async def generate(self, request: ActionRequest) -> ActionResponse:
        """Generate a legal document based on the action type and context."""
        template = _ACTION_TEMPLATES.get(request.action_type.value, "")

        prompt = (
            f"{template}\n\n"
            f"Situation/Context:\n{request.context}\n\n"
            "Generate the complete document ready for use."
        )

        try:
            content = await gemma_service.generate_text(
                prompt,
                language=request.language,
                system_instruction="You are a legal document drafting assistant. Generate professional, legally accurate documents.",
            )

            return ActionResponse(
                action_type=request.action_type.value,
                content=content,
                language=request.language,
                metadata={"case_id": request.case_id},
            )
        except Exception as e:
            logger.error(f"ActionAgent error: {e}")
            return ActionResponse(
                action_type=request.action_type.value,
                content="Unable to generate document. Please try again.",
                language=request.language,
            )


action_agent = ActionAgent()
