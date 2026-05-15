"""Precedent-Based Case Outcome Prediction API routes.

Accepts case details and predicts likely outcomes based on legal
precedents, landmark judgments, and statutory provisions for the relevant jurisdiction.
"""

import json
import re
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.gemma_service import gemma_service
from app.core.config import get_settings
from app.core.security import rate_limit_dependency, sanitize_input
from app.core.logging import logger
from app.models.schemas import LANGUAGE_NAMES

router = APIRouter(prefix="/api/predict", tags=["predict"])


# ── Schemas ──────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    case_description: str = Field(..., min_length=30, max_length=10000,
                                  description="Detailed description of the case / situation")
    case_type: str = Field(default="", max_length=100,
                           description="Category of case (e.g., Tenant Dispute, Employment, Consumer)")
    user_role: str = Field(default="", max_length=100,
                           description="User's role (tenant, employee, consumer, etc.)")
    language: str = Field(default="en")


# ── Predict ──────────────────────────────────────────────────────────────

@router.post("/outcome", dependencies=[Depends(rate_limit_dependency)])
async def predict_outcome(req: PredictRequest):
    """Predict case outcome based on legal precedents for the relevant jurisdiction."""
    case_desc = sanitize_input(req.case_description)
    case_type = sanitize_input(req.case_type) if req.case_type else "general"
    user_role = sanitize_input(req.user_role) if req.user_role else "petitioner"

    prompt = f"""You are an expert legal analyst specializing in case outcome prediction using precedent-based analysis across multiple jurisdictions.

CASE DETAILS:
Category: {case_type}
User's Role: {user_role}
Description:
\"\"\"
{case_desc[:8000]}
\"\"\"

Analyze this case thoroughly. Identify the most relevant Indian legal precedents (Supreme Court and High Court landmark judgments), applicable statutes, and predict the likely outcome.

Respond with ONLY a valid JSON object:

{{
  "prediction": {{
    "likely_outcome": "<FAVORABLE | UNFAVORABLE | MIXED | UNCERTAIN>",
    "confidence": <1-100>,
    "summary": "<2-3 sentence prediction summary>"
  }},
  "precedents": [
    {{
      "case_name": "<Party A vs Party B>",
      "court": "<Supreme Court of India / High Court name>",
      "year": "<year or approximate>",
      "citation": "<citation if known>",
      "relevance": "<how this case is relevant>",
      "held": "<what the court decided>",
      "impact_on_user": "<SUPPORTS | WEAKENS | NEUTRAL>"
    }}
  ],
  "applicable_laws": [
    {{
      "law": "<Act / Section name>",
      "section": "<specific section(s)>",
      "relevance": "<how this applies to the case>"
    }}
  ],
  "strengths": ["<factors in user's favor>"],
  "weaknesses": ["<factors against user>"],
  "recommended_arguments": ["<legal argument the user should make>"],
  "possible_outcomes": [
    {{
      "outcome": "<description of possible outcome>",
      "probability": "<HIGH | MEDIUM | LOW>",
      "conditions": "<under what circumstances>"
    }}
  ],
  "timeline_estimate": "<typical duration for such cases>",
  "next_steps": ["<recommended action>"],
  "disclaimer": "This is an AI-generated prediction based on legal precedents. It is not legal advice. Consult a qualified lawyer for professional guidance.",
  "references": [
    {{"title": "<official source name for the detected jurisdiction>", "uri": "<exact real URL from the official legal site of that country>"}}
  ]
}}

JURISDICTION-AWARE REFERENCE RULES:
- Include 3-5 authentic references with real, working URLs from the DETECTED JURISDICTION ONLY.
- India (default): indiankanoon.org, indiacode.nic.in, sci.gov.in, legislative.gov.in, labour.gov.in, consumeraffairs.nic.in, nalsa.gov.in, rtionline.gov.in, rera.gov.in
- USA: law.cornell.edu, uscode.house.gov, uscourts.gov, ftc.gov, dol.gov, consumerfinance.gov, justia.com
- UK: legislation.gov.uk, judiciary.uk, gov.uk, citizensadvice.org.uk, bailii.org
- Ukraine: zakon.rada.gov.ua, court.gov.ua, minjust.gov.ua
- EU: eur-lex.europa.eu, curia.europa.eu
- Australia: legislation.gov.au, austlii.edu.au, hcourt.gov.au
- Canada: laws-lois.justice.gc.ca, canlii.org, scc-csc.ca
- Other: official national parliament, supreme court, and government legal portal of that country.
- NEVER include Indian legal sites for non-Indian queries. NEVER include foreign sites for Indian queries.
- Prefer direct links to the specific Act, section, or case search page relevant to this case.

IMPORTANT:
- Cite REAL landmark cases from the detected jurisdiction wherever possible.
- Reference actual statutes and sections of law from that jurisdiction.
- Be realistic about confidence and probabilities.
- Consider the user's role ({user_role}) and analyze from their perspective.
- List at least 3-5 relevant precedents.
- Consider both favorable and unfavorable precedents.
- If the case type is common, reference well-known judgments."""

    try:
        # Build an optional instruction to write human-readable VALUES in the user's language
        # while ALWAYS keeping JSON keys in English (so parsing never breaks).
        lang_value_instruction = ""
        if req.language != "en":
            lang_name = LANGUAGE_NAMES.get(req.language, req.language)
            lang_value_instruction = (
                f" LANGUAGE RULE: All JSON keys MUST stay in English exactly as shown in the schema. "
                f"However, write every human-readable STRING VALUE in {lang_name} "
                f"(language code: '{req.language}'). This includes: summary, relevance, held, "
                f"conditions, outcome descriptions, strengths list items, weaknesses list items, "
                f"recommended_arguments list items, next_steps list items, timeline_estimate, "
                f"and disclaimer. "
                f"Do NOT translate: JSON keys, enum values (FAVORABLE/UNFAVORABLE/MIXED/UNCERTAIN/"
                f"HIGH/MEDIUM/LOW/SUPPORTS/WEAKENS/NEUTRAL), numbers, case citations, court names, "
                f"act names, or section numbers."
            )

        settings = get_settings()
        sources: list[dict] = []
        predict_system = (
            "You are an Indian legal case outcome predictor with deep knowledge of "
            "Supreme Court and High Court landmark judgments, Indian statutes, and legal principles. "
            "Use Google Search to verify every case name, citation, year, and section before quoting it. "
            "Respond with ONLY valid JSON. No markdown, no code blocks, no extra text. "
            f"Cite real Indian cases and laws. Be thorough and balanced in your analysis.{lang_value_instruction}"
        )
        if settings.USE_GOOGLE_SEARCH_GROUNDING:
            grounded = await gemma_service.generate_text_with_sources(
                prompt,
                language="en",  # JSON structure stays intact in English
                system_instruction=predict_system,
            )
            result = grounded["text"]
            sources = grounded.get("sources", [])
        else:
            result = await gemma_service.generate_text(
                prompt, language="en", system_instruction=predict_system,
            )

        analysis = _extract_json(result)
        if not analysis:
            analysis = {
                "prediction": {
                    "likely_outcome": "UNCERTAIN",
                    "confidence": 40,
                    "summary": result[:500],
                },
                "precedents": [],
                "applicable_laws": [],
                "strengths": [],
                "weaknesses": [],
                "recommended_arguments": [],
                "possible_outcomes": [],
                "timeline_estimate": "Varies depending on court and complexity.",
                "next_steps": ["Consult a qualified lawyer for detailed advice."],
                "disclaimer": "This is an AI-generated prediction. Consult a lawyer.",
            }

        # Ensure prediction block exists
        if "prediction" not in analysis:
            analysis["prediction"] = {
                "likely_outcome": "UNCERTAIN",
                "confidence": 40,
                "summary": analysis.get("summary", ""),
            }

        pred = analysis["prediction"]
        pred["confidence"] = max(1, min(100, int(pred.get("confidence", 40))))
        analysis["language"] = req.language
        # Prefer grounding sources; fall back to AI-generated references
        ai_refs = [
            {"title": r.get("title", ""), "uri": r.get("uri", "")}
            for r in analysis.get("references", [])
            if str(r.get("uri", "")).startswith("http")
        ]
        analysis["sources"] = sources if sources else ai_refs
        return analysis

    except Exception as e:
        logger.error(f"Case prediction error: {e}")
        return {
            "prediction": {
                "likely_outcome": "UNCERTAIN",
                "confidence": 0,
                "summary": "Unable to complete prediction. Please try again.",
            },
            "precedents": [],
            "applicable_laws": [],
            "strengths": [],
            "weaknesses": [],
            "recommended_arguments": [],
            "possible_outcomes": [],
            "timeline_estimate": "",
            "next_steps": [],
            "disclaimer": "This is an AI-generated prediction. Consult a lawyer.",
            "error": True,
        }


# ── Helper ───────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    cleaned = re.sub(r'```(?:json)?\s*', '', text)
    cleaned = re.sub(r'```\s*$', '', cleaned)
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None
