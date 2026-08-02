"""Tiny SQLite storage layer.

Uses the stdlib sqlite3 driver — no ORM. Each feature adds its own
`CREATE TABLE IF NOT EXISTS` to `init_db()` as it lands, so the schema
grows with the git history.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import get_settings


def _connect() -> sqlite3.Connection:
    settings = get_settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a connection, committing on success and rolling back on error."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables that don't exist yet. Safe to call on every startup."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS resumes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                source_filename TEXT NOT NULL,
                profile_json    TEXT NOT NULL,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- One row per (calendar day, company) that discovery has spent
            -- budget on. Enforces the "10 new companies per day" guardrail.
            CREATE TABLE IF NOT EXISTS company_daily (
                day           TEXT NOT NULL,
                company_key   TEXT NOT NULL,
                company_name  TEXT NOT NULL,
                first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (day, company_key)
            );
            """
        )
