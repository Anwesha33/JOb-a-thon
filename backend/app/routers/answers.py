"""Preview generated answers to application questions."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..models import AnswerRequest, AnswerResponse
from ..services import answers, opportunity_store, profiles

router = APIRouter(prefix="/api/answers", tags=["answers"])


@router.post("/generate", response_model=AnswerResponse)
def generate(req: AnswerRequest) -> AnswerResponse:
    profile = profiles.get_profile(req.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    opportunity = None
    if req.opportunity_id is not None:
        opportunity = opportunity_store.get_opportunity(req.opportunity_id)
        if opportunity is None:
            raise HTTPException(status_code=404, detail="Opportunity not found.")

    answer = answers.generate_answer(req.question, profile, opportunity)
    return AnswerResponse(
        question=req.question,
        answer=answer,
        source="llm" if get_settings().has_llm else "template",
    )
