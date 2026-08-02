"""Turn a search request into a deduped list of fresh opportunities.

This module owns the "what do we query" logic. It stays source-agnostic in
spirit but currently drives Adzuna. The per-day company budget and the
specific-company path are layered on in later features.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..models import Opportunity
from . import adzuna


def build_queries(role: Optional[str], keywords: Optional[list[str]]) -> list[str]:
    """Ordered, de-duplicated search terms derived from the request."""
    queries: list[str] = []
    if role and role.strip():
        queries.append(role.strip())
    for kw in keywords or []:
        if kw and kw.strip():
            queries.append(kw.strip())
    if not queries:
        # Last-resort default so an empty request still returns something.
        queries.append("software engineer")

    seen: set[str] = set()
    ordered: list[str] = []
    for q in queries:
        key = q.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(q)
    return ordered


async def discover(
    *,
    role: Optional[str] = None,
    location: Optional[str] = None,
    keywords: Optional[list[str]] = None,
    companies: Optional[list[str]] = None,
    limit: int = 100,
    max_days_old: int = 30,
    country: Optional[str] = None,
) -> list[Opportunity]:
    """Search and return up to `limit` fresh, de-duplicated openings.

    If `companies` is given, the search is restricted to those companies
    (one targeted query each). Otherwise it fans the derived queries across
    whatever companies the aggregator returns.
    """
    queries = build_queries(role, keywords)
    seen_ids: set[str] = set()
    found: list[Opportunity] = []

    def take(results: list[Opportunity]) -> bool:
        """Add new results; return True once the limit is reached."""
        for opp in results:
            if opp.external_id in seen_ids:
                continue
            seen_ids.add(opp.external_id)
            found.append(opp)
            if len(found) >= limit:
                return True
        return False

    cleaned_companies = [c.strip() for c in (companies or []) if c and c.strip()]

    if cleaned_companies:
        # Targeted: one query (the primary term) per named company.
        primary = queries[0]
        for company in cleaned_companies:
            results = await adzuna.search_jobs(
                what=primary,
                where=location,
                company=company,
                max_days_old=max_days_old,
                country=country,
            )
            if take(results):
                break
    else:
        # Broad: fan every derived query across all companies.
        for query in queries:
            results = await adzuna.search_jobs(
                what=query,
                where=location,
                max_days_old=max_days_old,
                country=country,
            )
            if take(results):
                break

    _sort_newest_first(found)
    return found


def _sort_newest_first(opps: list[Opportunity]) -> None:
    """Newest postings first; undated ones sink to the bottom."""
    opps.sort(key=lambda o: o.posted_date or date.min, reverse=True)
