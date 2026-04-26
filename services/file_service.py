"""File handling service for uploads."""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import validate_file_extension


class FileService:
    """Handle file uploads and storage."""

    def __init__(self):
        settings = get_settings()
        self._upload_dir = Path(settings.UPLOAD_DIR)
        self._max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self._allowed = settings.ALLOWED_EXTENSIONS
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> str:
        """Save an uploaded file and return the path."""
        if not file.filename:
            raise ValueError("No filename provided")

        if not validate_file_extension(file.filename, self._allowed):
            raise ValueError(f"File type not allowed. Accepted: {self._allowed}")

        content = await file.read()
        if len(content) > self._max_size:
            raise ValueError(f"File too large. Max {self._max_size // (1024*1024)} MB")

        ext = file.filename.rsplit(".", 1)[-1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        path = self._upload_dir / safe_name

        with open(path, "wb") as f:
            f.write(content)

        logger.info(f"Saved upload: {safe_name} ({len(content)} bytes)")
        return str(path)

    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        try:
            os.remove(path)
            return True
        except OSError:
            return False


file_service = FileService()
