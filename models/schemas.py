"""Pydantic models and schemas for the application."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Language ────────────────────────────────────────────────────────────────

class SupportedLanguage(str, Enum):
    EN = "en"
    HI = "hi"
    BN = "bn"
    TA = "ta"
    TE = "te"
    KN = "kn"
    MR = "mr"
    GU = "gu"
    OR = "or"
    BHO = "bho"
    SAT = "sat"   # Santali
    UK = "uk"     # Ukrainian


LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी",
    "bn": "বাংলা",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "kn": "ಕನ್ನಡ",
    "mr": "मराठी",
    "gu": "ગુજરાતી",
    "or": "ଓଡ଼ିଆ",
    "bho": "भोजपुरी",
    "sat": "ᱥᱟᱱᱛᱟᱲᱤ",
    "uk": "Українська",
}


# ── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en")
    session_id: Optional[str] = None
    mode: Optional[str] = Field(
        default=None,
        description="Optional client mode hint, e.g. 'voice' for the live voice chat "
                    "surface. Voice mode produces shorter, conversational replies "
                    "and skips the markdown sources block (bad for TTS).",
    )


class ChatResponse(BaseModel):
    reply: str
    language: str
    agent_used: str
    session_id: str
    metadata: Optional[dict] = None


# ── Document ────────────────────────────────────────────────────────────────

class DocumentAnalysis(BaseModel):
    summary: str
    risks: list[str]
    key_clauses: list[str]
    advice: str
    language: str = "en"


class DocumentUploadResponse(BaseModel):
    filename: str
    analysis: DocumentAnalysis
    session_id: str


# ── Case ────────────────────────────────────────────────────────────────────

class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Case(BaseModel):
    id: str
    title: str
    description: str
    status: CaseStatus = CaseStatus.OPEN
    language: str = "en"
    legal_domain: str = ""
    jurisdiction: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    documents: list[str] = []
    actions: list[str] = []
    deadlines: list[dict] = []


# ── Action ──────────────────────────────────────────────────────────────────

class ActionType(str, Enum):
    COMPLAINT_LETTER = "complaint_letter"
    LEGAL_NOTICE = "legal_notice"
    APPLICATION_FORM = "application_form"
    RTI_APPLICATION = "rti_application"


class ActionRequest(BaseModel):
    case_id: Optional[str] = None
    action_type: ActionType
    context: str = Field(..., min_length=1, max_length=5000)
    language: str = "en"


class ActionResponse(BaseModel):
    action_type: str
    content: str
    language: str
    metadata: Optional[dict] = None


# ── Intake ──────────────────────────────────────────────────────────────────

class IntakeResult(BaseModel):
    detected_language: str
    legal_domain: str
    jurisdiction: str
    urgency: str = "normal"
    entities: dict = {}
    summary: str = ""


# ── Rights Analysis ────────────────────────────────────────────────────────

class RightsAnalysis(BaseModel):
    legal_explanation: str
    section_references: list[str]
    simplified_explanation: str
    recommendations: list[str]
    language: str = "en"


# ── Follow-up ──────────────────────────────────────────────────────────────

class FollowUpInfo(BaseModel):
    case_id: str
    next_steps: list[str]
    deadlines: list[dict]
    recommendations: list[str]
    status_update: str
