"""Resolve an application question to an answer, or flag it for the user.

Resolution order:
  1. A direct profile field (name, email, phone, location).
  2. A cached answer the user gave earlier (within the last week).
  3. An essay-style question we can draft from the resume.
  4. Otherwise: needs the user, this once.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from ..models import Opportunity, Profile
from . import answers, question_cache

# (regex on the question, attribute on Profile)
_FIELD_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(full name|your name|name)\b", re.I), "name"),
    (re.compile(r"\b(e-?mail)\b", re.I), "email"),
    (re.compile(r"\b(phone|mobile|contact number)\b", re.I), "phone"),
    (re.compile(r"\b(location|city|where.*based|current location)\b", re.I), "location"),
]

# Questions we can draft from the resume rather than asking the user.
_ESSAY_HINTS = (
    "why", "describe", "tell us", "tell me", "explain", "strength", "weakness",
    "project", "experience", "challenge", "proud", "motivat", "interest",
    "fit", "cover letter", "about yourself", "suitable", "background",
    "accomplish", "achievement",
)


@dataclass
class Resolution:
    question: str
    answer: Optional[str]
    needs_input: bool
    source: str  # "profile" | "cache" | "resume" | "user"

    def as_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "needs_input": self.needs_input,
            "source": self.source,
        }


def _is_essay(question: str) -> bool:
    low = question.lower()
    return any(hint in low for hint in _ESSAY_HINTS)


def resolve(
    question: str,
    profile: Profile,
    opportunity: Optional[Opportunity] = None,
) -> Resolution:
    # 1. Direct profile field.
    for pattern, attr in _FIELD_PATTERNS:
        if pattern.search(question):
            value = getattr(profile, attr, None)
            if value:
                return Resolution(question, value, False, "profile")

    # 2. Something the user already answered this week.
    cached = question_cache.get(question)
    if cached is not None:
        return Resolution(question, cached, False, "cache")

    # 3. An essay-style question we can draft from the resume.
    if _is_essay(question):
        drafted = answers.generate_answer(question, profile, opportunity)
        return Resolution(question, drafted, False, "resume")

    # 4. Needs the user — just this once.
    return Resolution(question, None, True, "user")
