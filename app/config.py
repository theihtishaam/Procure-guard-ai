from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_environment() -> None:
    load_dotenv(ROOT_DIR / ".env.local", encoding="utf-8-sig")
    load_dotenv(ROOT_DIR / ".env", encoding="utf-8-sig")


class Settings(BaseModel):
    app_name: str = "ProcureGuard AI"
    host: str = "127.0.0.1"
    port: int = 8765
    aimlapi_api_key: str | None = Field(default=None)
    aimlapi_base_url: str = "https://api.aimlapi.com/v1"
    aimlapi_model_primary: str = "gpt-4o-mini"
    aimlapi_model_fast: str = "gpt-4o-mini"
    aimlapi_timeout_seconds: int = 45
    enable_live_llm: bool = True
    band_enabled: bool = False
    band_app_url: str = "https://app.band.ai"
    band_user_api_key: str | None = Field(default=None)


@lru_cache
def get_settings() -> Settings:
    load_environment()
    return Settings(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8765")),
        aimlapi_api_key=os.getenv("AIMLAPI_API_KEY"),
        aimlapi_base_url=os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1").rstrip("/"),
        aimlapi_model_primary=os.getenv("AIMLAPI_MODEL_PRIMARY", "gpt-4o-mini"),
        aimlapi_model_fast=os.getenv("AIMLAPI_MODEL_FAST", "gpt-4o-mini"),
        aimlapi_timeout_seconds=int(os.getenv("AIMLAPI_TIMEOUT_SECONDS", "45")),
        enable_live_llm=os.getenv("ENABLE_LIVE_LLM", "1").strip() not in {"0", "false", "False", "no"},
        band_enabled=os.getenv("BAND_ENABLED", "0").strip() in {"1", "true", "True", "yes"},
        band_app_url=os.getenv("BAND_APP_URL", "https://app.band.ai").rstrip("/"),
        band_user_api_key=os.getenv("BAND_USER_API_KEY"),
    )
