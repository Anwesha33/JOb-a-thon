"""Keep only openings whose title matches the role the user searched for.

Adzuna's keyword search (and our skill-based query fan-out) pulls in loosely
related roles — searching "SDE-1" can surface Product Manager or Data Analyst
postings. This module classifies the searched role into a family and requires
each opening's title to belong to that same family. Unknown roles fall back to
a token-overlap check so arbitrary titles still work.
"""
from __future__ import annotations

import re
from typing import Optional

# family -> (query aliases that map TO it, title keywords that identify it)
_FAMILIES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "software_engineer": (
        ("sde", "software engineer", "software developer",
         "software development engineer", "backend", "back end", "frontend",
         "front end", "full stack", "fullstack", "full-stack", "web developer",
         "application developer", "programmer", "swe", "mts",
         "member of technical staff"),
        ("software engineer", "software developer",
         "software development engineer", "sde", "backend", "back end",
         "back-end", "frontend", "front end", "front-end", "full stack",
         "fullstack", "full-stack", "web developer", "application developer",
         "programmer", "developer", "member of technical staff", "swe"),
    ),
    "mobile_engineer": (
        ("android", "ios", "mobile developer", "mobile engineer", "flutter",
         "react native"),
        ("android", "ios", "mobile developer", "mobile engineer", "flutter",
         "react native"),
    ),
    "data_scientist": (
        ("data scientist", "data science", "machine learning", "ml engineer",
         "ai engineer", "applied scientist", "research scientist", "nlp"),
        ("data scientist", "data science", "machine learning", "ml engineer",
         "ai engineer", "applied scientist", "research scientist"),
    ),
    "data_analyst": (
        ("data analyst", "business analyst", "bi analyst",
         "business intelligence", "analytics analyst", "reporting analyst"),
        ("data analyst", "business analyst", "bi analyst",
         "business intelligence analyst", "analytics analyst",
         "reporting analyst", "insights analyst"),
    ),
    "data_engineer": (
        ("data engineer", "data engineering", "etl", "big data"),
        ("data engineer", "data engineering", "etl developer"),
    ),
    "product_manager": (
        ("product manager", "product management", "product owner", "apm",
         "associate product manager", "group product manager", "product lead"),
        ("product manager", "product management", "product owner",
         "product lead", "apm", "group product"),
    ),
    "designer": (
        ("ux designer", "ui designer", "product designer", "ux/ui",
         "ui/ux", "visual designer", "graphic designer", "ux researcher"),
        ("designer", "ux researcher"),
    ),
    "devops_sre": (
        ("devops", "sre", "site reliability", "platform engineer",
         "infrastructure engineer", "cloud engineer"),
        ("devops", "sre", "site reliability", "platform engineer",
         "infrastructure engineer", "cloud engineer"),
    ),
    "qa_engineer": (
        ("qa engineer", "quality assurance", "test engineer", "sdet",
         "automation tester"),
        ("qa engineer", "quality assurance", "test engineer", "sdet",
         "automation test", "qa analyst"),
    ),
}

# Broad Adzuna query term(s) for each family, so a narrow role like "SDE-1"
# still pulls in the wider pool of on-role postings (then filtered by title).
_FAMILY_QUERIES: dict[str, tuple[str, ...]] = {
    "software_engineer": ("software engineer", "software developer"),
    "mobile_engineer": ("mobile developer", "android developer"),
    "data_scientist": ("data scientist", "machine learning engineer"),
    "data_analyst": ("data analyst", "business analyst"),
    "data_engineer": ("data engineer",),
    "product_manager": ("product manager",),
    "designer": ("product designer", "ux designer"),
    "devops_sre": ("devops engineer", "site reliability engineer"),
    "qa_engineer": ("qa engineer", "sdet"),
}


def family_query_terms(family: Optional[str]) -> list[str]:
    """Broad search terms that reliably surface a family's postings."""
    return list(_FAMILY_QUERIES.get(family, ()))


_LEVEL_STOPWORDS = {
    "i", "ii", "iii", "iv", "1", "2", "3", "sr", "jr", "senior", "junior",
    "associate", "lead", "staff", "principal", "the", "and", "for", "of", "a",
    "an", "role", "position", "openings", "opening", "job", "jobs",
}


def _normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return " " + re.sub(r"\s+", " ", text).strip() + " "


def classify_role_family(role: Optional[str]) -> Optional[str]:
    """Map a searched role to a known family, or None if unrecognized."""
    if not role:
        return None
    norm = _normalize(role)
    for family, (aliases, _) in _FAMILIES.items():
        for alias in aliases:
            a = _normalize(alias).strip()
            if f" {a} " in norm:
                return family
    return None


def _significant_tokens(role: str) -> list[str]:
    tokens = _normalize(role).split()
    return [t for t in tokens if len(t) >= 3 and t not in _LEVEL_STOPWORDS]


def title_matches_role(title: str, role: Optional[str], family: Optional[str]) -> bool:
    """True if `title` is relevant to the searched role.

    - Known family: the title must contain one of that family's keywords.
    - Unknown role: the title must share a significant token with the role.
    - No role at all: everything passes.
    """
    if not role:
        return True
    low = _normalize(title)
    if family:
        _, keywords = _FAMILIES[family]
        return any(f" {kw} " in low or kw in low for kw in keywords)
    tokens = _significant_tokens(role)
    if not tokens:
        return True
    return any(t in low for t in tokens)
