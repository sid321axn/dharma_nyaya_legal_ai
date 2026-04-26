"""Document Agent — uses Gemma multimodal API for document analysis."""

import json
from typing import Optional
from app.services.gemma_service import gemma_service
from app.models.schemas import DocumentAnalysis
from app.core.logging import logger


class DocumentAgent:
    """Analyze uploaded documents (images, PDFs)."""

    async def analyze(self, file_path: str, language: str = "en",
                      custom_prompt: Optional[str] = None) -> DocumentAnalysis:
        """Analyze a document and return structured analysis."""
        prompt = custom_prompt or (
            "Analyze this legal document thoroughly. Provide your response as a JSON object with:\n"
            '- "summary": A clear summary of the document\n'
            '- "risks": An array of legal risks or concerns found\n'
            '- "key_clauses": An array of important clauses or sections\n'
            '- "advice": Practical advice for the person holding this document\n\n'
            "Respond ONLY with valid JSON."
        )

        try:
            response = await gemma_service.analyze_document(file_path, prompt, language)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            data = json.loads(response)
            return DocumentAnalysis(
                summary=data.get("summary", ""),
                risks=data.get("risks", []),
                key_clauses=data.get("key_clauses", []),
                advice=data.get("advice", ""),
                language=language,
            )
        except json.JSONDecodeError:
            # If Gemma returns non-JSON, wrap the text response
            return DocumentAnalysis(
                summary=response[:500] if response else "Unable to parse document.",
                risks=["Could not extract structured risks — see summary."],
                key_clauses=[],
                advice="Please consult a legal professional for detailed analysis.",
                language=language,
            )
        except Exception as e:
            logger.error(f"DocumentAgent error: {e}")
            return DocumentAnalysis(
                summary="Document analysis failed.",
                risks=["Analysis error — please try again."],
                key_clauses=[],
                advice="Please try uploading the document again.",
                language=language,
            )


document_agent = DocumentAgent()
