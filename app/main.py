"""DHARMA-NYAYA — AI Legal Empowerment Platform
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.routes import chat, document, case, language
from app.api.routes import action, tts, report, quiz, docgen, compare, predict
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered multilingual legal assistant platform",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(chat.router)
app.include_router(document.router)
app.include_router(case.router)
app.include_router(language.router)
app.include_router(action.router)
app.include_router(tts.router)
app.include_router(report.router)
app.include_router(quiz.router)
app.include_router(docgen.router)
app.include_router(compare.router)
app.include_router(predict.router)

# Static files
frontend_dir = Path(__file__).parent.parent / "frontend"
images_dir = Path(__file__).parent.parent / "images"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")
if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

if frontend_dir.exists():
    @app.get("/")
    async def serve_landing():
        return FileResponse(str(frontend_dir / "index.html"))

    @app.get("/chat")
    async def serve_chat():
        return FileResponse(str(frontend_dir / "chat.html"))

    @app.get("/dashboard")
    async def serve_dashboard():
        return FileResponse(str(frontend_dir / "dashboard.html"))

    @app.get("/sos")
    async def serve_sos():
        return FileResponse(str(frontend_dir / "sos.html"))

    @app.get("/quiz")
    async def serve_quiz():
        return FileResponse(str(frontend_dir / "quiz.html"))

    @app.get("/legal-aid")
    async def serve_legal_aid():
        return FileResponse(str(frontend_dir / "legal-aid.html"))

    @app.get("/legal-docs")
    async def serve_legal_docs():
        return FileResponse(str(frontend_dir / "legal-docs.html"))

    @app.get("/voice")
    async def serve_voice():
        return FileResponse(str(frontend_dir / "voice.html"))

    @app.get("/spot-the-trap")
    async def serve_spot_the_trap():
        return FileResponse(str(frontend_dir / "spot-the-trap.html"))

    @app.get("/predict")
    async def serve_predict():
        return FileResponse(str(frontend_dir / "predict.html"))

    @app.get("/offline-rights")
    async def serve_offline_rights():
        return FileResponse(str(frontend_dir / "offline-rights.html"))

    @app.get("/offline-guides")
    async def serve_offline_guides():
        return FileResponse(str(frontend_dir / "offline-guides.html"))

    @app.get("/manifest.json")
    async def serve_manifest():
        return FileResponse(str(frontend_dir / "manifest.json"), media_type="application/manifest+json")

    @app.get("/sw.js")
    async def serve_sw():
        return FileResponse(str(frontend_dir / "sw.js"), media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/"})


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.on_event("startup")
async def startup():
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    # Ensure upload directory exists
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
