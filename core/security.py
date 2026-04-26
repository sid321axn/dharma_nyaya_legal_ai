"""Security utilities: rate limiting, file validation, input sanitization."""

import re
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, client_ip: str) -> bool:
        """Return True if request is allowed."""
        now = time.time()
        window_start = now - self.window_seconds
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]
        if len(self._requests[client_ip]) >= self.max_requests:
            return False
        self._requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter()


async def rate_limit_dependency(request: Request) -> None:
    """FastAPI dependency for rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")


def validate_file_extension(filename: str, allowed: str = "jpg,jpeg,png,pdf") -> bool:
    """Validate that file extension is allowed."""
    allowed_set = {ext.strip().lower() for ext in allowed.split(",")}
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed_set


def sanitize_input(text: str) -> str:
    """Basic input sanitization — strip control characters."""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text).strip()
