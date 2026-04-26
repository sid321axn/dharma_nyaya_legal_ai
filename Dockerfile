# ── Stage 1: Build ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps needed to compile wheels (e.g. httptools for uvicorn[standard])
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ───────────────────────────────────────────────────────────
FROM python:3.12-slim

# Non-root user for Cloud Run security best-practice
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY app/       app/
COPY frontend/  frontend/
COPY images/    images/
COPY fonts/     fonts/

# quiz_translations.db is read-only lookup data — safe to bake into image.
# NOTE: Cloud Run filesystem is ephemeral; any runtime writes are lost on restart.
COPY quiz_translations.db .

# Create uploads dir; files are deleted immediately after analysis so this is safe.
RUN mkdir -p uploads && chown -R appuser:appuser /app

USER appuser

# Cloud Run injects $PORT (default 8080). Never hardcode 8080 — always read $PORT.
ENV PORT=8080
EXPOSE 8080

# Single worker — Cloud Run scales via instances, not intra-process workers.
# Using a shell form so $PORT is expanded at runtime.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --log-level info"]
