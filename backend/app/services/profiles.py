"""Persistence for parsed resume profiles."""
from __future__ import annotations

from ..db import get_conn
from ..models import Profile


def save_profile(profile: Profile) -> Profile:
    """Insert a profile and return it with its assigned id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO resumes (source_filename, profile_json) VALUES (?, ?)",
            (profile.source_filename, profile.model_dump_json()),
        )
        profile.id = int(cur.lastrowid)
    return profile


def update_profile(profile: Profile) -> Profile:
    """Persist changes to an already-saved profile."""
    if profile.id is None:
        return save_profile(profile)
    with get_conn() as conn:
        conn.execute(
            "UPDATE resumes SET profile_json = ? WHERE id = ?",
            (profile.model_dump_json(), profile.id),
        )
    return profile


def get_profile(profile_id: int) -> Profile | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, profile_json FROM resumes WHERE id = ?", (profile_id,)
        ).fetchone()
    if row is None:
        return None
    profile = Profile.model_validate_json(row["profile_json"])
    profile.id = row["id"]
    return profile


def latest_profile() -> Profile | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, profile_json FROM resumes ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if row is None:
        return None
    profile = Profile.model_validate_json(row["profile_json"])
    profile.id = row["id"]
    return profile
