"""Application configuration, loaded from environment / .env.

Nothing about a specific person or role lives here — search parameters
(role, location, companies) are supplied per-request from the UI so the
tool stays generic. This file only holds service-level settings.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/  -> repo root is one level up from this file's parent.
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Adzuna jobs API (https://developer.adzuna.com/)
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "in"

    # Optional: answer generation via the Claude API.
    anthropic_api_key: str = ""

    # Guardrails.
    daily_company_limit: int = 10
    freshness_days: int = 30

    # Storage.
    database_path: Path = DATA_DIR / "jobathon.db"

    @property
    def has_adzuna(self) -> bool:
        return bool(self.adzuna_app_id and self.adzuna_app_key)

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    settings = Settings()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return settings
