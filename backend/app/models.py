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
    resume_path: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    experience_years: Optional[float] = None
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


# Application-pipeline status for a stored opportunity.
STATUS_NEW = "new"
STATUS_SELECTED = "selected"
STATUS_APPLIED = "applied"
STATUS_NEEDS_INPUT = "needs_input"
STATUS_ERROR = "error"

# Statuses the user can set from the applications dashboard, in pipeline order.
APPLICATION_STATUSES = ["applied", "interviewing", "offer", "rejected"]


class StoredOpportunity(Opportunity):
    """An opportunity persisted in the DB, with an internal id and status."""

    id: int
    status: str = STATUS_NEW
    discovered_at: Optional[str] = None
    applied_at: Optional[str] = None


class SearchRequest(BaseModel):
    """Parameters for a discovery run — all supplied from the UI."""

    role: Optional[str] = None
    location: Optional[str] = None
    companies: list[str] = Field(default_factory=list)
    profile_id: Optional[int] = None
    limit: int = 100
    country: Optional[str] = None
    # Candidate's years of experience. If null, the resume's estimate is used.
    experience_years: Optional[float] = None


class SearchResponse(BaseModel):
    opportunities: list[StoredOpportunity]
    budget: dict
    count: int


class AnswerRequest(BaseModel):
    question: str
    profile_id: int
    opportunity_id: Optional[int] = None


class AnswerResponse(BaseModel):
    question: str
    answer: str
    source: str  # "llm" or "template"


class QuestionResolveRequest(BaseModel):
    question: str
    profile_id: int
    opportunity_id: Optional[int] = None


class QuestionResolveResponse(BaseModel):
    question: str
    answer: Optional[str] = None
    needs_input: bool
    source: str  # "profile" | "cache" | "resume" | "user"


class QuestionAnswerRequest(BaseModel):
    question: str
    answer: str


class QuestionAnswerResponse(BaseModel):
    stored: bool
    expires_at: str

