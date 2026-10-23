"""
config.py — Application settings loaded from environment variables.

All settings are typed and validated at startup using pydantic-settings.
If a required variable is missing, the app exits with a clear error message.
No value is hardcoded in any logic file — everything flows through this module.
"""

from __future__ import annotations

from typing import List

from pydantic import Field, field_validator, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment & Auth Mode ─────────────────────────────
    env: str = Field("development", description="development | staging | production")
    auth_mode: str = Field(
        "dev",
        description="Auth mode: 'dev' (bypasses auth with default dev user) or 'supabase' (enforces JWT)",
    )

    # ── Database ─────────────────────────────────────────────
    # Use the Supabase TRANSACTION POOLER (port 6543, pgBouncer).
    # Render may not reach the direct connection (port 5432) via IPv6.
    # Find it: Supabase Dashboard → Project Settings → Database
    #           → Connection pooling → Transaction mode → URI
    database_url: str = Field(
        "postgresql://postgres:postgres@localhost:5432/postgres",
        description=(
            "PostgreSQL connection URL. Use Supabase transaction pooler "
            "(port 6543) for Render deployments."
        ),
    )

    # ── Supabase ──────────────────────────────────────────────
    supabase_url: str = Field("https://example.supabase.co", description="Supabase project URL")

    # Accept both SUPABASE_ANON_KEY (preferred) and legacy SUPABASE_PUBLISHABLE_KEY
    supabase_anon_key: str = Field(
        "dummy-anon-key",
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "SUPABASE_PUBLISHABLE_KEY"),
        description="Supabase public anon key (safe to use server-side for auth verification)",
    )

    # Service-role key — server side only, never in frontend.
    # Accept both SUPABASE_SERVICE_KEY and legacy SUPABASE_SECRET_KEY.
    supabase_service_key: str = Field(
        "",
        validation_alias=AliasChoices("SUPABASE_SERVICE_KEY", "SUPABASE_SECRET_KEY"),
        description="Supabase service role key (used for storage; optional now)",
    )

    # ── LLM ──────────────────────────────────────────────────
    llm_provider: str = Field("gemini", description="LLM provider: gemini")

    gemini_api_key: str = Field(
        "dummy-gemini-key",
        description="Google Gemini API key from https://aistudio.google.com/",
    )

    # Default to current GA model 'gemini-2.0-flash' (or 'gemini-1.5-flash').
    # Configurable via GEMINI_MODEL in .env.
    gemini_model: str = Field(
        "gemini-2.0-flash",
        description="Gemini model name (e.g. gemini-2.0-flash, gemini-1.5-flash)",
    )

    llm_timeout_seconds: int = Field(60, description="LLM request timeout in seconds")

    # Controls the thinking budget for Gemini 2.0+ models supporting thinking.
    # Values: none (0), low (1024), medium (8192), high (24576)
    llm_thinking_level: str = Field(
        "none",
        description="Thinking level: none | low | medium | high",
    )

    # ── CORS ─────────────────────────────────────────────────
    # Comma-separated. Add your Vercel URL here.
    allowed_origins: str = Field(
        "http://localhost:5173",
        description="Comma-separated allowed CORS origins",
    )

    # ── Rate limiting ─────────────────────────────────────────
    daily_ai_generation_limit: int = Field(
        20,
        description="Max AI generations per user per day (protects shared API key)",
    )

    # ── Computed properties ───────────────────────────────────

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated origins. Always includes localhost:5173."""
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        if "http://localhost:5173" not in origins:
            origins.append("http://localhost:5173")
        return origins

    @property
    def async_database_url(self) -> str:
        """
        Convert a standard postgresql:// URL to the asyncpg driver format.
        asyncpg requires postgresql+asyncpg:// or postgres+asyncpg://.
        """
        url = self.database_url
        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url[len("postgresql://"):]
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[len("postgres://"):]
        return url  # Already has the correct prefix

    @property
    def thinking_budget(self) -> int:
        """Map thinking level name to a numeric budget for Gemini."""
        mapping = {
            "none": 0,
            "low": 1024,
            "medium": 8192,
            "high": 24576,
        }
        return mapping.get(self.llm_thinking_level.lower(), 0)

    # ── Validators ────────────────────────────────────────────

    @field_validator("gemini_api_key")
    @classmethod
    def gemini_key_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "GEMINI_API_KEY is required but not set. "
                "Get your key at https://aistudio.google.com/ and add it to .env"
            )
        return v.strip()

    @field_validator("database_url")
    @classmethod
    def database_url_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "DATABASE_URL is required. "
                "Use the Supabase transaction pooler URL (port 6543)."
            )
        return v.strip()

    @field_validator("supabase_url")
    @classmethod
    def supabase_url_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("SUPABASE_URL is required.")
        return v.strip()


# Loaded once at module import time. Import `settings` everywhere.
settings = Settings()
