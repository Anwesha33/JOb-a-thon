"""Adzuna jobs API client.

Docs: https://developer.adzuna.com/  (free app_id + app_key)

We lean on Adzuna's own `max_days_old` filter for freshness and
`sort_by=date` so the newest postings come first, then re-check the
`created` date client-side as a belt-and-braces guard.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

import httpx

from ..config import get_settings
from ..models import Opportunity

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaError(RuntimeError):
    """Raised when Adzuna is unreachable, unauthorized, or misconfigured."""


async def search_jobs(
    *,
    what: str,
    where: Optional[str] = None,
    max_days_old: int = 30,
    results_per_page: int = 50,
    page: int = 1,
    company: Optional[str] = None,
    country: Optional[str] = None,
) -> list[Opportunity]:
    """Query one page of Adzuna results and normalize them.

    `company`, when given, is folded into the free-text query — Adzuna has
    no dedicated company filter, so results are also filtered client-side.
    """
    settings = get_settings()
    if not settings.has_adzuna:
        raise AdzunaError(
            "Adzuna is not configured. Set ADZUNA_APP_ID and ADZUNA_APP_KEY "
            "in your .env (free key at https://developer.adzuna.com/)."
        )

    country = (country or settings.adzuna_country or "in").lower()
    query = what if not company else f"{what} {company}".strip()

    params: dict[str, Any] = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "what": query,
        "results_per_page": max(1, min(results_per_page, 50)),
        "max_days_old": max_days_old,
        "sort_by": "date",
        "content-type": "application/json",
    }
    if where:
        params["where"] = where

    url = f"{BASE_URL}/{country}/search/{max(1, page)}"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise AdzunaError(f"Could not reach Adzuna: {exc}") from exc

    if resp.status_code == 401:
        raise AdzunaError("Adzuna rejected the credentials (401). Check keys.")
    if resp.status_code == 429:
        raise AdzunaError("Adzuna rate limit hit (429). Try again later.")
    if resp.status_code >= 400:
        raise AdzunaError(f"Adzuna returned {resp.status_code}: {resp.text[:200]}")

    payload = resp.json()
    opportunities: list[Opportunity] = []
    for raw in payload.get("results", []):
        opp = _normalize(raw)
        if opp is None:
            continue
        # Client-side freshness guard.
        if opp.days_old is not None and opp.days_old > max_days_old:
            continue
        # Client-side company filter when a specific company was requested.
        if company and company.lower() not in opp.company.lower():
            continue
        opportunities.append(opp)
    return opportunities


def _normalize(raw: dict[str, Any]) -> Optional[Opportunity]:
    external_id = str(raw.get("id") or "").strip()
    title = (raw.get("title") or "").strip()
    url = (raw.get("redirect_url") or "").strip()
    if not external_id or not title or not url:
        return None

    company = ((raw.get("company") or {}).get("display_name") or "Unknown").strip()
    location = (raw.get("location") or {}).get("display_name")

    return Opportunity(
        source="adzuna",
        external_id=external_id,
        title=title,
        company=company,
        location=location,
        posted_date=_parse_date(raw.get("created")),
        url=url,
        description=_snippet(raw.get("description")),
        salary_min=raw.get("salary_min"),
        salary_max=raw.get("salary_max"),
        contract_time=raw.get("contract_time"),
    )


def _parse_date(value: Any) -> Optional[date]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _snippet(text: Any, limit: int = 320) -> Optional[str]:
    if not text or not isinstance(text, str):
        return None
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
