"""Feedback API — collect user feedback (name, rating, message, location) into MySQL."""

from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import logger

router = APIRouter(prefix="/api", tags=["feedback"])


class FeedbackIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    page: Optional[str] = Field(default=None, max_length=120)
    rating: int = Field(..., ge=1, le=5)
    message: Optional[str] = Field(default=None, max_length=4000)
    location: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def _mysql_enabled() -> bool:
    s = get_settings()
    return bool(s.DB_HOST and s.DB_USER and s.DB_NAME)


def _mysql_conn():
    import pymysql
    s = get_settings()
    return pymysql.connect(
        host=s.DB_HOST, port=s.DB_PORT, user=s.DB_USER, password=s.DB_PASSWORD,
        database=s.DB_NAME, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5, read_timeout=10,
    )


def _ensure_table() -> None:
    """Create feedback table on first use (cheap if it already exists)."""
    try:
        conn = _mysql_conn()
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    name        VARCHAR(120),
                    page        VARCHAR(120),
                    rating      TINYINT      NOT NULL,
                    message     TEXT,
                    location    VARCHAR(255),
                    latitude    DECIMAL(10,7),
                    longitude   DECIMAL(10,7),
                    user_agent  VARCHAR(255),
                    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_created (created_at)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"feedback table ensure failed: {e}")


@router.post("/feedback")
async def submit_feedback(payload: FeedbackIn, request: Request):
    if not _mysql_enabled():
        raise HTTPException(status_code=503, detail="Feedback storage is not configured")

    _ensure_table()
    ua = (request.headers.get("user-agent") or "")[:255]

    try:
        conn = _mysql_conn()
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO feedback "
                "(name, page, rating, message, location, latitude, longitude, user_agent) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    payload.name, payload.page, payload.rating, payload.message,
                    payload.location, payload.latitude, payload.longitude, ua,
                ),
            )
            new_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"ok": True, "id": new_id}
    except Exception as e:
        logger.error(f"Feedback insert failed: {e}")
        raise HTTPException(status_code=500, detail="Could not save feedback")


@router.get("/feedback/recent")
async def recent_feedback(limit: int = 20):
    """Return the latest feedback entries (admin / dashboard use)."""
    if not _mysql_enabled():
        return {"items": []}
    limit = max(1, min(limit, 100))
    try:
        conn = _mysql_conn()
        with conn.cursor() as c:
            c.execute(
                "SELECT id, name, page, rating, message, location, created_at "
                "FROM feedback ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            rows = c.fetchall()
        conn.close()
        # Convert datetime to ISO string
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return {"items": rows}
    except Exception as e:
        logger.error(f"Feedback list failed: {e}")
        return {"items": []}


@router.get("/feedback/all")
async def all_feedback(
    limit: int = 500,
    valid_only: bool = True,
    min_rating: int = 1,
):
    """Return all feedback entries for the admin viewer.

    By default returns only "valid" feedback — entries with a non-empty
    message and a rating >= ``min_rating``. Set ``valid_only=false`` to
    include every record.
    """
    if not _mysql_enabled():
        return {"items": [], "total": 0, "configured": False}

    limit = max(1, min(limit, 2000))
    min_rating = max(1, min(min_rating, 5))

    where = []
    params: list = []
    if valid_only:
        where.append("message IS NOT NULL AND TRIM(message) <> ''")
        where.append("rating >= %s")
        params.append(min_rating)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    try:
        conn = _mysql_conn()
        with conn.cursor() as c:
            c.execute(
                f"SELECT id, name, page, rating, message, location, "
                f"latitude, longitude, created_at "
                f"FROM feedback {where_sql} "
                f"ORDER BY created_at DESC LIMIT %s",
                tuple(params + [limit]),
            )
            rows = c.fetchall()
            c.execute(f"SELECT COUNT(*) AS n FROM feedback {where_sql}", tuple(params))
            total = (c.fetchone() or {}).get("n", 0)
        conn.close()

        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
            # Decimal -> float for JSON
            if r.get("latitude") is not None:
                r["latitude"] = float(r["latitude"])
            if r.get("longitude") is not None:
                r["longitude"] = float(r["longitude"])

        return {"items": rows, "total": int(total), "configured": True}
    except Exception as e:
        logger.error(f"Feedback list (all) failed: {e}")
        raise HTTPException(status_code=500, detail="Could not load feedback")
