"""Application settings (P01 contract).

Single source of runtime configuration. Read from environment / .env.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Vertex AI Express mode API key (https://cloud.google.com/vertex-ai/...
    # /start/express-mode). Used by the google-genai SDK with vertexai=True.
    google_api_key: str = ""
    google_model: str = "gemini-2.5-flash"
    db_path: str = "./data/project.db"
    # Team Tech Capability Catalog (Alteryx/UiPath/Power Apps) + task->tool matching.
    # On by default; set TECH_CATALOG_ENABLED=false to disable it (e.g. for a demo that
    # should not surface or choose the team tools).
    tech_catalog_enabled: bool = True
    # Per-request timeout (seconds) for the Gemini client; guards single-threaded
    # PoC requests against a hung/slow API call.
    request_timeout: float = 60.0
    # Comma-separated list of allowed CORS origins for the Vite dev server.
    cors_origins: str = "http://localhost:5173"
    # Max accepted size (bytes) for an uploaded attachment (docx/xlsx). Guards
    # the single-threaded PoC against pulling a huge file fully into memory.
    max_upload_bytes: int = 10 * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
