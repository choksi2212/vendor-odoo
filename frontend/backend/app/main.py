import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import auth, users
from app.core.config import settings
from app.core.security import limiter
from app.db.base import Base
from app.db.session import SessionLocal, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

_CLEANUP_INTERVAL_SECONDS = 3600


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cors_headers(request: Request) -> dict:
    """
    Build CORS headers for the incoming request's origin.
    Included manually in every exception handler so that error responses
    always carry the header — even when Starlette's ServerErrorMiddleware
    would normally bypass CORSMiddleware's send-wrapper.
    """
    origin = request.headers.get("origin", "")
    if origin in settings.allowed_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }
    return {}


# ── Background cleanup ────────────────────────────────────────────────────────

async def _cleanup_expired_records() -> None:
    """Hourly background task — removes expired OTPs and spent one-time tokens."""
    from app.models.user import OneTimeToken, OTPCode

    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            deleted_otps = (
                db.query(OTPCode)
                .filter(OTPCode.expires_at < now)
                .delete(synchronize_session=False)
            )
            deleted_tokens = (
                db.query(OneTimeToken)
                .filter(OneTimeToken.expires_at < now, OneTimeToken.is_used.is_(True))
                .delete(synchronize_session=False)
            )
            db.commit()
            logger.info(
                "Cleanup: removed %d expired OTPs, %d used tokens.",
                deleted_otps,
                deleted_tokens,
            )
        except Exception:
            logger.error("Cleanup task failed.", exc_info=True)
            db.rollback()
        finally:
            db.close()


# ── Schema migrations ─────────────────────────────────────────────────────────

def _run_schema_migrations() -> None:
    """
    Idempotent migrations for columns that SQLAlchemy create_all cannot add
    to already-existing tables.
    """
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'users' AND column_name = 'is_2fa_enabled'"
        ))
        if result.fetchone() is None:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE"
            ))
            conn.commit()
            logger.info("Migration applied: users.is_2fa_enabled column added.")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    _run_schema_migrations()
    logger.info("Database schema verified.")
    cleanup_task = asyncio.create_task(_cleanup_expired_records())
    yield
    cleanup_task.cancel()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Arial Sense Auth API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.state.limiter = limiter

app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(users.router)


# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Please try again later."},
        headers=_cors_headers(request),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred."},
        headers=_cors_headers(request),
    )
