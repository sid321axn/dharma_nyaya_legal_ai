"""In-memory database for demo/development. Replace with real DB in production."""

from datetime import datetime
from typing import Optional
import uuid


# In-memory stores
_cases: dict[str, dict] = {}
_sessions: dict[str, list[dict]] = {}


def generate_id() -> str:
    """Generate a unique ID."""
    return uuid.uuid4().hex[:12]


# ── Cases ───────────────────────────────────────────────────────────────────

def create_case(title: str, description: str, language: str = "en",
                legal_domain: str = "", jurisdiction: str = "") -> dict:
    """Create a new case record."""
    case_id = generate_id()
    case = {
        "id": case_id,
        "title": title,
        "description": description,
        "status": "open",
        "language": language,
        "legal_domain": legal_domain,
        "jurisdiction": jurisdiction,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "documents": [],
        "actions": [],
        "deadlines": [],
    }
    _cases[case_id] = case
    return case


def get_case(case_id: str) -> Optional[dict]:
    """Get a case by ID."""
    return _cases.get(case_id)


def update_case(case_id: str, **kwargs) -> Optional[dict]:
    """Update case fields."""
    case = _cases.get(case_id)
    if case:
        case.update(kwargs)
        case["updated_at"] = datetime.utcnow().isoformat()
    return case


def list_cases() -> list[dict]:
    """List all cases."""
    return list(_cases.values())


# ── Sessions ────────────────────────────────────────────────────────────────

def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get or create a chat session."""
    if session_id and session_id in _sessions:
        return session_id
    new_id = generate_id()
    _sessions[new_id] = []
    return new_id


def add_message(session_id: str, role: str, content: str) -> None:
    """Add a message to session history."""
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    })


def get_history(session_id: str, limit: int = 20) -> list[dict]:
    """Get recent chat history for a session."""
    return _sessions.get(session_id, [])[-limit:]
