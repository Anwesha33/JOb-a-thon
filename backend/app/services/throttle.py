"""Daily company budget.

Rule: discovery may spend budget on at most N *distinct* companies per
calendar day (default 10). Companies already spent-on today are "free" to
keep surfacing; brand-new companies are only admitted while budget remains.
The ledger persists, so repeated searches in a day accumulate toward the
cap instead of resetting, and a new day starts fresh.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..config import get_settings
from ..db import get_conn
from ..models import Opportunity


@dataclass
class BudgetStatus:
    day: str
    limit: int
    companies_used: int

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.companies_used)

    def as_dict(self) -> dict:
        return {
            "day": self.day,
            "limit": self.limit,
            "companies_used": self.companies_used,
            "remaining": self.remaining,
        }


def _today() -> str:
    return date.today().isoformat()


def _key(company: str) -> str:
    return " ".join(company.strip().lower().split())


def companies_used_today(day: Optional[str] = None) -> set[str]:
    day = day or _today()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT company_key FROM company_daily WHERE day = ?", (day,)
        ).fetchall()
    return {r["company_key"] for r in rows}


def _reserve(day: str, companies: list[tuple[str, str]]) -> None:
    """Persist newly spent-on companies as (key, display_name) pairs."""
    if not companies:
        return
    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO company_daily (day, company_key, company_name) "
            "VALUES (?, ?, ?)",
            [(day, key, name) for key, name in companies],
        )


def budget_status(
    day: Optional[str] = None, limit: Optional[int] = None
) -> BudgetStatus:
    day = day or _today()
    limit = limit if limit is not None else get_settings().daily_company_limit
    return BudgetStatus(day=day, limit=limit, companies_used=len(companies_used_today(day)))


def apply_daily_budget(
    opportunities: list[Opportunity],
    *,
    limit: Optional[int] = None,
    day: Optional[str] = None,
) -> tuple[list[Opportunity], BudgetStatus]:
    """Admit opportunities until the day's distinct-company cap is reached.

    `opportunities` should already be ordered by preference (newest first),
    because that order decides which companies win the remaining budget.
    Returns the admitted subset and the resulting budget status.
    """
    day = day or _today()
    limit = limit if limit is not None else get_settings().daily_company_limit

    used = companies_used_today(day)
    newly: list[tuple[str, str]] = []
    admitted: list[Opportunity] = []

    for opp in opportunities:
        key = _key(opp.company)
        if key in used:
            admitted.append(opp)
        elif len(used) < limit:
            used.add(key)
            newly.append((key, opp.company.strip()))
            admitted.append(opp)
        # else: budget exhausted for new companies — skip this opening.

    _reserve(day, newly)
    return admitted, BudgetStatus(day=day, limit=limit, companies_used=len(used))
