"""Estimate years of experience and match openings to a seniority level.

The estimate is best-effort: an explicit "5 years of experience" wins; otherwise
we sum employment date ranges found in the resume. The result is used both to
show the candidate their detected experience and to filter out openings that are
clearly the wrong level.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional

# Ordered seniority ranks shared by candidates and job titles.
_RANK = {"entry": 0, "junior": 1, "mid": 2, "senior": 3, "lead": 4}

_EXPLICIT_PATTERNS = [
    re.compile(r"(\d{1,2}(?:\.\d)?)\s*\+?\s*years?(?:\s+of)?\s+(?:experience|exp)\b", re.I),
    re.compile(r"\b(?:experience|exp)\s*[:\-]?\s*(\d{1,2}(?:\.\d)?)\s*\+?\s*years?", re.I),
]
_RANGE_RE = re.compile(
    r"((?:19|20)\d{2})\s*[-–—]{1,3}\s*(present|current|(?:19|20)\d{2})", re.I
)


def estimate_years(text: str) -> Optional[float]:
    """Best-effort years of professional experience from resume text."""
    if not text:
        return None

    for pattern in _EXPLICIT_PATTERNS:
        m = pattern.search(text)
        if m:
            years = float(m.group(1))
            if 0 < years <= 50:
                return years

    # Fall back to summing employment date ranges.
    this_year = date.today().year
    total = 0
    for start, end in _RANGE_RE.findall(text):
        s = int(start)
        e = this_year if end.lower() in ("present", "current") else int(end)
        span = e - s
        if 0 < span <= 15:  # ignore absurd spans (likely not a single job)
            total += span
    return float(total) if total > 0 else None


def candidate_band(years: Optional[float]) -> Optional[str]:
    if years is None:
        return None
    if years < 1:
        return "entry"
    if years < 3:
        return "junior"
    if years < 6:
        return "mid"
    if years < 9:
        return "senior"
    return "lead"


# Title keywords, most-senior first so "senior staff" matches "lead".
_TITLE_BANDS = [
    ("lead", ("principal", "staff", " lead", "lead ", "head ", "director", "vp ",
              "vice president", "architect", "manager")),
    ("senior", ("senior", "sr.", "sr ")),
    ("entry", ("intern", "trainee", "graduate", "fresher", "entry level",
               "entry-level")),
    ("junior", ("junior", "jr.", "jr ")),
]


def title_band(title: str) -> Optional[str]:
    low = f" {title.lower()} "
    for band, kws in _TITLE_BANDS:
        if any(kw in low for kw in kws):
            return band
    return None  # unspecified — treat as broadly compatible


def is_compatible(years: Optional[float], title: str) -> bool:
    """Is this title a reasonable level for a candidate with `years` experience?

    Lenient: unknown experience or an unlabeled title always passes; otherwise
    the title must be within one seniority rank of the candidate.
    """
    cand = candidate_band(years)
    if cand is None:
        return True
    tband = title_band(title)
    if tband is None:
        return True
    return abs(_RANK[tband] - _RANK[cand]) <= 1
