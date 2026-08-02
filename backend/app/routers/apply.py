"""Assisted-apply endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import STATUS_APPLIED
from ..services import apply, opportunity_store, profiles

router = APIRouter(prefix="/api/apply", tags=["apply"])


class ApplyRequest(BaseModel):
    opportunity_id: int
    profile_id: int
    headless: bool = False


@router.post("")
def start(req: ApplyRequest) -> dict:
    opportunity = opportunity_store.get_opportunity(req.opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    profile = profiles.get_profile(req.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    job_id = uuid.uuid4().hex
    job = apply.start_apply(job_id, opportunity, profile, headless=req.headless)
    opportunity_store.set_status(req.opportunity_id, STATUS_APPLIED)
    return {"job_id": job.id, "status": job.status}


@router.get("/{job_id}")
def status(job_id: str) -> dict:
    job = apply.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Apply job not found.")
    return {
        "job_id": job.id,
        "opportunity_id": job.opportunity_id,
        "status": job.status,
        "message": job.message,
        "plan": job.plan,
        "pending_questions": job.pending_questions,
    }
