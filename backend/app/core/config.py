import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ───────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str
    DATABASE_TEST_URL: str = ""

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str
    JWT_SECRET_KEY: str = ""  # If not set, uses SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5500"

    # ── Application URLs ──────────────────────────────────────────────────────
    APP_BASE_URL: str = "http://localhost:5500"

    # ── Email (Brevo HTTP API) ────────────────────────────────────────────────
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = ""
    BREVO_SENDER_NAME: str = "VendorBridge"
    MAIL_FROM: str = ""  # Fallback to BREVO_SENDER_EMAIL
    MAIL_FROM_NAME: str = ""  # Fallback to BREVO_SENDER_NAME

    # ── Company Information ───────────────────────────────────────────────────
    COMPANY_NAME: str = "VendorBridge"
    COMPANY_ADDRESS: str = "123 Business Park, Mumbai, India 400001"
    COMPANY_PHONE: str = "+91-9876543210"
    COMPANY_EMAIL: str = "contact@vendorbridge.com"
    COMPANY_GSTIN: str = "27AABCU9603R1Z0"

    # ── Storage Paths ─────────────────────────────────────────────────────────
    PDF_STORAGE_PATH: str = "generated_pdfs"
    UPLOAD_STORAGE_PATH: str = "uploads"

    # ── File Upload ───────────────────────────────────────────────────────────
    MAX_FILE_SIZE: int = 10485760  # 10MB in bytes
    ALLOWED_EXTENSIONS: str = '[".pdf",".doc",".docx",".xls",".xlsx"]'

    # ── Tax Configuration ─────────────────────────────────────────────────────
    TAX_RATE: float = 18.0  # GST rate in percentage

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Password Policy ───────────────────────────────────────────────────────
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # ── Account Security ──────────────────────────────────────────────────────
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCK_DURATION_MINUTES: int = 30

    # ── OTP Configuration ─────────────────────────────────────────────────────
    OTP_EXPIRY_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 3

    # ── Redis (optional) ──────────────────────────────────────────────────────
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

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Parse ALLOWED_EXTENSIONS string into a list."""
        try:
            return json.loads(self.ALLOWED_EXTENSIONS)
        except json.JSONDecodeError:
            return [".pdf", ".doc", ".docx", ".xls", ".xlsx"]

    @property
    def jwt_secret(self) -> str:
        """Return JWT secret key, fallback to SECRET_KEY if not set."""
        return self.JWT_SECRET_KEY or self.SECRET_KEY

    @property
    def email_from(self) -> str:
        """Return email sender address."""
        return self.MAIL_FROM or self.BREVO_SENDER_EMAIL

    @property
    def email_from_name(self) -> str:
        """Return email sender name."""
        return self.MAIL_FROM_NAME or self.BREVO_SENDER_NAME

    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Alias for allowed_origins for backward compatibility."""
        return self.allowed_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
