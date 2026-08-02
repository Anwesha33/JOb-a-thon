"""FastAPI application entrypoint.

Run locally with:  uvicorn app.main:app --reload  (from the backend/ dir)
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="JOb-a-thon",
    version=__version__,
    summary="Resume-driven job discovery and assisted apply.",
    lifespan=lifespan,
)

# The React dev server runs on a different origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    """Liveness probe plus a peek at which integrations are configured."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "adzuna_configured": settings.has_adzuna,
        "llm_configured": settings.has_llm,
        "daily_company_limit": settings.daily_company_limit,
        "freshness_days": settings.freshness_days,
    }
