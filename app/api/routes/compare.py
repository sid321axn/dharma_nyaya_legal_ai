"""Document Comparison ("Spot the Trap") API routes.

Compares two legal documents / contract texts and identifies:
  - Unfair / exploitative clauses
  - Missing protections for the user
  - Hidden risks and ambiguous language
  - Deviations from standard / fair templates
"""

import io
import json
import re
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel, Field

from app.services.gemma_service import gemma_service
from app.core.config import get_settings
from app.core.security import rate_limit_dependency, sanitize_input
from app.core.logging import logger

router = APIRouter(prefix="/api/compare", tags=["compare"])


# ── Schemas ──────────────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    doc_a: str = Field(..., min_length=20, max_length=15000,
                       description="Primary document text (the one being reviewed)")
    doc_b: str = Field(default="", max_length=15000,
                       description="Reference/fair template text (optional)")
    doc_type: str = Field(default="", max_length=100,
                          description="Type of document, e.g., rental agreement, employment contract")
    language: str = Field(default="en")


class SingleDocReviewRequest(BaseModel):
    document: str = Field(..., min_length=20, max_length=15000)
    doc_type: str = Field(default="", max_length=100)
    language: str = Field(default="en")


ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/msword",  # .doc (fallback label)
}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


def _extract_pdf_text(data: bytes) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _extract_docx_text(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


# ── File Upload → Extract Text ──────────────────────────────────────────

@router.post("/extract", dependencies=[Depends(rate_limit_dependency)])
async def extract_file_text(file: UploadFile = File(...)):
    """Upload a PDF or Word (.docx) file and return extracted plain text."""
    if file.content_type not in ALLOWED_TYPES and not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(400, "Only PDF and Word (.docx) files are supported.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(400, "File too large. Maximum size is 5 MB.")

    try:
        if file.filename.lower().endswith(".pdf") or file.content_type == "application/pdf":
            text = _extract_pdf_text(data)
        elif file.filename.lower().endswith(".docx"):
            text = _extract_docx_text(data)
        else:
            raise HTTPException(400, "Unsupported file format. Please upload a PDF or .docx file.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File extraction error: {e}")
        raise HTTPException(500, f"Could not extract text from file: {e}")

    if not text or len(text.strip()) < 10:
        raise HTTPException(400, "Could not extract meaningful text from the file. Try pasting the text instead.")

    return {"text": text.strip(), "characters": len(text.strip()), "filename": file.filename}


# ── Compare Two Documents ────────────────────────────────────────────────

@router.post("/compare", dependencies=[Depends(rate_limit_dependency)])
async def compare_documents(req: CompareRequest):
    """Compare two legal documents and identify traps, risks, and missing protections."""
    doc_a = sanitize_input(req.doc_a)
    doc_b = sanitize_input(req.doc_b) if req.doc_b else ""
    doc_type = sanitize_input(req.doc_type) if req.doc_type else "legal document"

    if doc_b:
        prompt = f"""You are an expert legal document analyst protecting consumers and common citizens.

Compare these two documents. Document A is the one being reviewed (potentially unfair). Document B is the reference/fair version.

DOCUMENT A (Under Review):
\"\"\"
{doc_a[:6000]}
\"\"\"

DOCUMENT B (Fair Reference):
\"\"\"
{doc_b[:6000]}
\"\"\"

Document Type: {doc_type}

Analyze Document A against Document B and respond with ONLY a valid JSON object:

{{
  "overall_risk": "<low|medium|high|critical>",
  "risk_score": <1-100>,
  "summary": "<2-3 sentence summary of the comparison>",
  "traps": [
    {{
      "clause": "<exact problematic text from Document A>",
      "risk_level": "<low|medium|high|critical>",
      "issue": "<what's wrong with this clause>",
      "fair_version": "<what Document B says or what a fair clause would look like>",
      "impact": "<how this could hurt the person signing>"
    }}
  ],
  "missing_protections": [
    {{
      "protection": "<what's missing>",
      "importance": "<why this matters>",
      "standard_clause": "<what should be included>"
    }}
  ],
  "safe_clauses": ["<clause that is fair and standard>"],
  "recommendations": ["<action recommendation>"],
  "legal_references": ["<relevant Indian law/section>"]
}}

Be thorough. Find ALL traps and unfair terms. Protect the common citizen."""
    else:
        prompt = f"""You are an expert legal document analyst protecting consumers and common citizens.

Review this {doc_type} document and identify ALL unfair clauses, hidden risks, and missing protections.

DOCUMENT (Under Review):
\"\"\"
{doc_a[:8000]}
\"\"\"

Document Type: {doc_type}

Analyze this document from the perspective of protecting the weaker party (tenant, employee, consumer, borrower, etc.). Respond with ONLY a valid JSON object:

{{
  "overall_risk": "<low|medium|high|critical>",
  "risk_score": <1-100>,
  "summary": "<2-3 sentence overall assessment>",
  "traps": [
    {{
      "clause": "<exact problematic text from the document>",
      "risk_level": "<low|medium|high|critical>",
      "issue": "<what's wrong with this clause>",
      "fair_version": "<what a fair version of this clause would say>",
      "impact": "<how this could hurt the person signing>"
    }}
  ],
  "missing_protections": [
    {{
      "protection": "<what's missing>",
      "importance": "<why this matters>",
      "standard_clause": "<what should be included>"
    }}
  ],
  "safe_clauses": ["<clause that is fair and standard>"],
  "recommendations": ["<action recommendation>"],
  "legal_references": ["<relevant Indian law/section>"]
}}

Be thorough and specific. Quote exact text from the document. Protect the common citizen."""

    try:
        settings = get_settings()
        sources: list[dict] = []
        validations: list[dict] = []
        compare_system = (
            "You are a legal document comparison expert specializing in Indian law. "
            "Your job is to protect common citizens from unfair contracts and agreements. "
            "Use Google Search to verify references against current Indian Acts "
            "(Indian Contract Act, Consumer Protection Act, IT Act, RERA, etc.) and recent judgments. "
            "Respond with ONLY valid JSON. No markdown, no code blocks, no extra text. "
            "Be specific — quote exact clauses. Be thorough — find every trap."
        )
        if settings.USE_GOOGLE_SEARCH_GROUNDING:
            grounded = await gemma_service.generate_text_with_sources(
                prompt, language=req.language, system_instruction=compare_system,
            )
            result = grounded["text"]
            sources = grounded.get("sources", [])
            validations = grounded.get("validations", [])
        else:
            result = await gemma_service.generate_text(
                prompt, language=req.language, system_instruction=compare_system,
            )

        analysis = _extract_json(result)
        if not analysis:
            analysis = {
                "overall_risk": "medium",
                "risk_score": 50,
                "summary": result[:500],
                "traps": [],
                "missing_protections": [],
                "safe_clauses": [],
                "recommendations": [],
                "legal_references": [],
            }

        # Clamp
        analysis["risk_score"] = max(1, min(100, int(analysis.get("risk_score", 50))))
        analysis["language"] = req.language
        analysis["mode"] = "compare" if doc_b else "review"
        analysis["sources"] = sources
        return analysis

    except Exception as e:
        logger.error(f"Document comparison error: {e}")
        return {
            "overall_risk": "medium",
            "risk_score": 50,
            "summary": "Unable to complete analysis. Please try again.",
            "traps": [],
            "missing_protections": [],
            "safe_clauses": [],
            "recommendations": [],
            "legal_references": [],
            "error": True,
        }


# ── Quick Single-Doc Review ──────────────────────────────────────────────

@router.post("/review", dependencies=[Depends(rate_limit_dependency)])
async def review_document(req: SingleDocReviewRequest):
    """Quick review of a single document for traps and risks."""
    compare_req = CompareRequest(
        doc_a=req.document,
        doc_b="",
        doc_type=req.doc_type,
        language=req.language,
    )
    return await compare_documents(compare_req)


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
