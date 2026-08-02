"""Applications dashboard — track everything you've applied to."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import APPLICATION_STATUSES, StoredOpportunity
from ..services import opportunity_store

router = APIRouter(prefix="/api/applications", tags=["applications"])


class StatusUpdate(BaseModel):
    status: str


@router.get("")
def list_applications() -> dict:
    apps = opportunity_store.list_applications()
    summary = {s: 0 for s in APPLICATION_STATUSES}
    for a in apps:
        if a.status in summary:
            summary[a.status] += 1
    summary["total"] = len(apps)
    return {"applications": apps, "summary": summary, "statuses": APPLICATION_STATUSES}


@router.post("/{opportunity_id}/status", response_model=StoredOpportunity)
def update_status(opportunity_id: int, body: StatusUpdate) -> StoredOpportunity:
    if body.status not in APPLICATION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of {APPLICATION_STATUSES}.",
        )
    opp = opportunity_store.get_opportunity(opportunity_id)
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    opportunity_store.set_status(opportunity_id, body.status)
    return opportunity_store.get_opportunity(opportunity_id)
