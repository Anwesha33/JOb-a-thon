"""Resume upload + retrieval endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..config import DATA_DIR
from ..models import Profile
from ..services import profiles
from ..services.resume_parser import parse_resume

router = APIRouter(prefix="/api/resume", tags=["resume"])

MAX_BYTES = 8 * 1024 * 1024  # 8 MB is plenty for a resume.
UPLOAD_DIR = DATA_DIR / "uploads"


@router.post("/upload", response_model=Profile)
async def upload_resume(file: UploadFile = File(...)) -> Profile:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 8 MB).")

    try:
        profile = parse_resume(file.filename or "resume", data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - parser edge cases
        raise HTTPException(
            status_code=422,
            detail=f"Could not read that resume: {exc}",
        ) from exc

    profile = profiles.save_profile(profile)

    # Keep the original file so the apply engine can attach it to forms.
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "resume").suffix or ".pdf"
    dest = UPLOAD_DIR / f"{profile.id}{suffix}"
    dest.write_bytes(data)
    profile.resume_path = str(dest)
    return profiles.update_profile(profile)


@router.get("/{profile_id}", response_model=Profile)
def get_resume(profile_id: int) -> Profile:
    profile = profiles.get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile
