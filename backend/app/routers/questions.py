"""Resolve application questions and remember user-supplied answers."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import (
    QuestionAnswerRequest,
    QuestionAnswerResponse,
    QuestionResolveRequest,
    QuestionResolveResponse,
)
from ..services import opportunity_store, profiles, qa, question_cache

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/resolve", response_model=QuestionResolveResponse)
def resolve(req: QuestionResolveRequest) -> QuestionResolveResponse:
    profile = profiles.get_profile(req.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    opportunity = None
    if req.opportunity_id is not None:
        opportunity = opportunity_store.get_opportunity(req.opportunity_id)

    result = qa.resolve(req.question, profile, opportunity)
    return QuestionResolveResponse(**result.as_dict())


@router.post("/answer", response_model=QuestionAnswerResponse)
def answer(req: QuestionAnswerRequest) -> QuestionAnswerResponse:
    """Remember a user's answer to an otherwise-unanswerable question."""
    expires_at = question_cache.put(req.question, req.answer)
    return QuestionAnswerResponse(stored=True, expires_at=expires_at)


@router.get("/cache")
def cache() -> list[dict]:
    return question_cache.list_all()
