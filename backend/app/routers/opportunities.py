"""Opportunity discovery and listing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..models import SearchRequest, SearchResponse, StoredOpportunity
from ..services import discovery, opportunity_store, profiles, throttle
from ..services.adzuna import AdzunaError

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Discover fresh openings for a role/location (and optionally specific
    companies), spend the daily company budget, and persist the results."""
    settings = get_settings()

    keywords: list[str] = []
    experience_years = req.experience_years
    if req.profile_id is not None:
        profile = profiles.get_profile(req.profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found.")
        keywords = profile.search_keywords()
        # Fall back to the resume's estimate when not explicitly provided.
        if experience_years is None:
            experience_years = profile.experience_years

    try:
        raw = await discovery.discover(
            role=req.role,
            location=req.location,
            keywords=keywords,
            companies=req.companies,
            limit=req.limit,
            max_days_old=settings.freshness_days,
            country=req.country,
            experience_years=experience_years,
        )
    except AdzunaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    admitted, status = throttle.apply_daily_budget(raw)
    stored = opportunity_store.upsert_many(admitted)

    return SearchResponse(
        opportunities=stored,
        budget=status.as_dict(),
        count=len(stored),
    )


@router.get("", response_model=list[StoredOpportunity])
def list_all(status: str | None = None) -> list[StoredOpportunity]:
    """List already-discovered opportunities, newest first."""
    return opportunity_store.list_opportunities(status=status)


@router.get("/budget")
def budget() -> dict:
    """Today's company budget usage."""
    return throttle.budget_status().as_dict()
