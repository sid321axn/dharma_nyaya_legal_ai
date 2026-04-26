"""Quiz API — serves pre-translated quiz questions from SQLite."""

import json
import sqlite3
from pathlib import Path
from fastapi import APIRouter, Query
from app.core.logging import logger

router = APIRouter(prefix="/api", tags=["quiz"])

DB_PATH = str(Path(__file__).parent.parent.parent.parent / "quiz_translations.db")


def _get_db():
    """Get a SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/quiz/questions")
async def get_quiz_questions(language: str = Query(default="en", max_length=10)):
    """
    Return ALL quiz questions for a given language, grouped by topic.
    Questions are pre-translated and stored in SQLite — instant response.
    """
    try:
        conn = _get_db()
        c = conn.cursor()

        # Check if requested language exists, fallback to English
        c.execute("SELECT COUNT(*) FROM quiz_questions WHERE language=?", (language,))
        count = c.fetchone()[0]
        if count == 0:
            language = "en"

        c.execute(
            "SELECT topic, question_index, question, options, answer_index, explanation "
            "FROM quiz_questions WHERE language=? ORDER BY topic, question_index",
            (language,)
        )
        rows = c.fetchall()
        conn.close()

        # Group by topic
        topics = {}
        for row in rows:
            topic = row["topic"]
            if topic not in topics:
                topics[topic] = []
            topics[topic].append({
                "q": row["question"],
                "opts": json.loads(row["options"]),
                "ans": row["answer_index"],
                "explain": row["explanation"],
            })

        return {"language": language, "topics": topics}

    except Exception as e:
        logger.error(f"Quiz DB error: {e}")
        return {"language": "en", "topics": {}}


@router.get("/quiz/languages")
async def get_quiz_languages():
    """Return list of languages available in the quiz DB."""
    try:
        conn = _get_db()
        c = conn.cursor()
        c.execute("SELECT DISTINCT language FROM quiz_questions ORDER BY language")
        langs = [row[0] for row in c.fetchall()]
        conn.close()
        return {"languages": langs}
    except Exception as e:
        logger.error(f"Quiz languages error: {e}")
        return {"languages": ["en"]}
