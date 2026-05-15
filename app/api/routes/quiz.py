"""Quiz API — serves quiz questions from MySQL (preferred) or SQLite (fallback).

If DB_HOST is set, the route reads from MySQL on every request, so updating
the question bank only requires INSERT/UPDATE — no image rebuild. If MySQL is
unreachable or unconfigured, falls back to the bundled `quiz_translations.db`.
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.core.logging import logger

router = APIRouter(prefix="/api", tags=["quiz"])

SQLITE_PATH = str(Path(__file__).parent.parent.parent.parent / "quiz_translations.db")


# ── MySQL helpers ─────────────────────────────────────────────────────────────

def _mysql_enabled() -> bool:
    s = get_settings()
    return bool(s.DB_HOST and s.DB_USER and s.DB_NAME)


def _mysql_conn():
    import pymysql
    s = get_settings()
    return pymysql.connect(
        host=s.DB_HOST,
        port=s.DB_PORT,
        user=s.DB_USER,
        password=s.DB_PASSWORD,
        database=s.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
        read_timeout=10,
    )


def _query_mysql(language: str) -> Optional[Dict[str, Any]]:
    try:
        conn = _mysql_conn()
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) AS n FROM quiz_questions WHERE language=%s", (language,))
            if (c.fetchone() or {}).get("n", 0) == 0:
                language = "en"
            c.execute(
                "SELECT topic, question_index, question, options, answer_index, explanation "
                "FROM quiz_questions WHERE language=%s ORDER BY topic, question_index",
                (language,),
            )
            rows = c.fetchall()
        conn.close()

        topics: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            topics.setdefault(row["topic"], []).append({
                "q": row["question"],
                "opts": json.loads(row["options"]),
                "ans": row["answer_index"],
                "explain": row["explanation"],
            })
        return {"language": language, "topics": topics}
    except Exception as e:
        logger.warning(f"MySQL quiz read failed, falling back to SQLite: {e}")
        return None


def _list_languages_mysql() -> Optional[List[str]]:
    try:
        conn = _mysql_conn()
        with conn.cursor() as c:
            c.execute("SELECT DISTINCT language FROM quiz_questions ORDER BY language")
            langs = [r["language"] for r in c.fetchall()]
        conn.close()
        return langs
    except Exception as e:
        logger.warning(f"MySQL language list failed, falling back to SQLite: {e}")
        return None


# ── SQLite fallback ───────────────────────────────────────────────────────────

def _sqlite_conn():
    if not os.path.exists(SQLITE_PATH):
        return None
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _query_sqlite(language: str) -> Dict[str, Any]:
    conn = _sqlite_conn()
    if conn is None:
        return {"language": language, "topics": {}}
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM quiz_questions WHERE language=?", (language,))
    if c.fetchone()[0] == 0:
        language = "en"
    c.execute(
        "SELECT topic, question_index, question, options, answer_index, explanation "
        "FROM quiz_questions WHERE language=? ORDER BY topic, question_index",
        (language,),
    )
    rows = c.fetchall()
    conn.close()
    topics: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        topics.setdefault(row["topic"], []).append({
            "q": row["question"],
            "opts": json.loads(row["options"]),
            "ans": row["answer_index"],
            "explain": row["explanation"],
        })
    return {"language": language, "topics": topics}


def _list_languages_sqlite() -> List[str]:
    conn = _sqlite_conn()
    if conn is None:
        return ["en"]
    c = conn.cursor()
    c.execute("SELECT DISTINCT language FROM quiz_questions ORDER BY language")
    langs = [row[0] for row in c.fetchall()]
    conn.close()
    return langs


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/quiz/questions")
async def get_quiz_questions(language: str = Query(default="en", max_length=10)):
    """Return ALL quiz questions for a language, grouped by topic."""
    try:
        if _mysql_enabled():
            result = _query_mysql(language)
            if result is not None:
                return result
        return _query_sqlite(language)
    except Exception as e:
        logger.error(f"Quiz fetch error: {e}")
        return {"language": "en", "topics": {}}


@router.get("/quiz/languages")
async def get_quiz_languages():
    """Return list of languages available in the quiz store."""
    try:
        if _mysql_enabled():
            langs = _list_languages_mysql()
            if langs is not None:
                return {"languages": langs}
        return {"languages": _list_languages_sqlite()}
    except Exception as e:
        logger.error(f"Quiz languages error: {e}")
        return {"languages": ["en"]}
