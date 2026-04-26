"""Document upload and analysis API route."""

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from app.models.schemas import DocumentUploadResponse, DocumentAnalysis
from app.agents.document_agent import document_agent
from app.services.file_service import file_service
from app.models.database import get_or_create_session
from app.core.security import rate_limit_dependency

router = APIRouter(prefix="/api/document", tags=["document"])


@router.post("/upload", response_model=DocumentUploadResponse,
             dependencies=[Depends(rate_limit_dependency)])
async def upload_document(
    file: UploadFile = File(...),
    language: str = Form(default="en"),
    session_id: str = Form(default=""),
) -> DocumentUploadResponse:
    """Upload and analyze a legal document."""
    try:
        file_path = await file_service.save_upload(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    analysis = await document_agent.analyze(file_path, language=language)
    sid = get_or_create_session(session_id or None)

    # Clean up uploaded file after analysis
    file_service.delete_file(file_path)

    return DocumentUploadResponse(
        filename=file.filename or "unknown",
        analysis=analysis,
        session_id=sid,
    )
