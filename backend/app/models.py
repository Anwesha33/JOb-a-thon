"""Shared pydantic schemas."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class Profile(BaseModel):
    """A structured view of the candidate, extracted from their resume.

    Kept generic: the UI can override role/location at search time, so a
    thin or messy resume still works.
    """

    id: Optional[int] = None
    source_filename: str = ""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    raw_text: str = ""

    def search_keywords(self) -> list[str]:
        """Best guesses for what to search job boards with."""
        keywords: list[str] = []
        if self.headline:
            keywords.append(self.headline)
        keywords.extend(self.roles)
        # Skills make decent fallback keywords when no role is obvious.
        keywords.extend(self.skills[:5])
        # De-dupe while preserving order.
        seen: set[str] = set()
        out: list[str] = []
        for kw in keywords:
            key = kw.strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(kw.strip())
        return out


class Opportunity(BaseModel):
    """A single job opening, normalized from whatever source found it."""

    source: str = "adzuna"
    external_id: str
    title: str
    company: str
    location: Optional[str] = None
    posted_date: Optional[date] = None
    url: str
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    contract_time: Optional[str] = None

    @property
    def days_old(self) -> Optional[int]:
        if self.posted_date is None:
            return None
        return (date.today() - self.posted_date).days

