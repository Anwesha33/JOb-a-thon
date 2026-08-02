"""A time-boxed cache for user-supplied answers.

When an application asks something the resume can't answer (expected salary,
notice period, visa status, ...), the user answers once and we remember it for
a week, keyed by a normalized form of the question.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..db import get_conn

CACHE_DAYS = 7


def _key(question: str) -> str:
    """Normalize a question so trivially different phrasings collide."""
    text = question.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    return re.sub(r"\s+", " ", text)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get(question: str) -> Optional[str]:
    """Return a cached answer if present and unexpired; else None."""
    key = _key(question)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT answer, expires_at FROM question_cache WHERE question_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        if datetime.fromisoformat(row["expires_at"]) <= _now():
            conn.execute(
                "DELETE FROM question_cache WHERE question_key = ?", (key,)
            )
            return None
        return row["answer"]


def put(question: str, answer: str, days: int = CACHE_DAYS) -> str:
    """Store an answer for `days` days. Returns the ISO expiry timestamp."""
    expires_at = (_now() + timedelta(days=days)).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO question_cache (question_key, question, answer, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(question_key) DO UPDATE SET
                question=excluded.question,
                answer=excluded.answer,
                created_at=datetime('now'),
                expires_at=excluded.expires_at
            """,
            (_key(question), question, answer, expires_at),
        )
    return expires_at


def purge_expired() -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM question_cache WHERE expires_at <= ?", (_now().isoformat(),)
        )
        return cur.rowcount


def list_all() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT question, answer, expires_at FROM question_cache "
            "ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]
