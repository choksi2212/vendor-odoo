import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Stored as a plain string so pydantic-settings never tries to json.loads()
    # it. Use .allowed_origins to get the parsed list everywhere in the app.
    # Accepts either JSON array or comma-separated values:
    #   JSON:  ["https://a.com","https://b.com"]
    #   CSV:   https://a.com,https://b.com
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5500"

    # ── Frontend base URL (used to build email links) ─────────────────────────
    APP_BASE_URL: str = "http://localhost:5500"

    # ── Email (Brevo HTTP API — no SMTP, works on Railway, free Gmail sender) ─
    BREVO_API_KEY: str = ""
    MAIL_FROM: str = ""        # set to your verified Gmail in Railway
    MAIL_FROM_NAME: str = "Arial Sense"

    # ── Redis (optional — in-memory fallback if empty) ────────────────────────
    REDIS_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS string into a list regardless of format.

        Strips trailing slashes from each origin so that values like
        'https://example.com/' match the browser's 'Origin: https://example.com'
        header, which never includes a trailing slash.
        """
        v = self.ALLOWED_ORIGINS.strip()
        if not v:
            return []
        if v.startswith("["):
            try:
                raw = json.loads(v)
            except json.JSONDecodeError:
                raw = [o.strip() for o in v.split(",") if o.strip()]
        else:
            raw = [o.strip() for o in v.split(",") if o.strip()]
        return [o.rstrip("/") for o in raw]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
