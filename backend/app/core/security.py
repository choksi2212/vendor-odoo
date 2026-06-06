import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Use Redis-backed storage when REDIS_URL is set, otherwise fall back to in-memory.
# In production with multiple workers REDIS_URL must be configured.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL if settings.REDIS_URL else "memory://",
)


def hash_password(password: str) -> str:
    """Hash password using bcrypt with automatic salt generation.
    
    Bcrypt has a 72-byte limit. Passwords are truncated to 72 bytes
    as per standard bcrypt behavior. Our password policy (max 128 chars)
    ensures this is never an issue in practice.
    """
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    plain_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)


def create_access_token(subject: dict[str, Any] | str) -> str:
    """Create access token. Subject can be a dict or string (user_id)."""
    if isinstance(subject, str):
        payload = {"sub": subject}
    else:
        payload = subject
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type": "access"})
    
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def create_2fa_pending_token(user_id: str) -> str:
    """Short-lived JWT used as a session handle between password verification and OTP verification."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "2fa_pending"},
        settings.jwt_secret,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload


def decode_2fa_pending_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "2fa_pending":
        raise JWTError("Invalid token type")
    return payload
