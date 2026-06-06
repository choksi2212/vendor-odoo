"""
Authentication service — all business logic for VendorBridge auth system.

Responsibilities:
  - signup / email verification / resend verification
  - login (with email-verification gate + optional 2FA)
  - OTP generation and verification (2FA)
  - refresh token rotation
  - logout
  - forgot / reset password

Email sending is always fire-and-forget via FastAPI BackgroundTasks.
The service returns (email, raw_token) tuples so the API layer can schedule
the background send without any raw tokens passing through logs.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_2fa_pending_token,
    create_access_token,
    create_refresh_token,
    decode_2fa_pending_token,
    hash_password,
    verify_password,
)
from app.models.user import OneTimeToken, OTPCode, TokenPurpose, User, UserSession
from app.schemas.auth import LoginRequest, ResetPasswordRequest, SignupRequest

logger = logging.getLogger(__name__)

_MAX_FAILED_ATTEMPTS = settings.MAX_LOGIN_ATTEMPTS
_LOCK_DURATION_MINUTES = settings.ACCOUNT_LOCK_DURATION_MINUTES
_MAX_OTP_ATTEMPTS = settings.OTP_MAX_ATTEMPTS
_OTP_EXPIRE_MINUTES = settings.OTP_EXPIRY_MINUTES
_EMAIL_TOKEN_EXPIRE_HOURS = 24
_RESET_TOKEN_EXPIRE_HOURS = 1


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _hash_token(token: str) -> str:
    """SHA-256 hash a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _verify_otp_hash(otp: str, stored_hash: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return hmac.compare_digest(
        hashlib.sha256(otp.encode()).hexdigest(),
        stored_hash,
    )


def _generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


# ─── Signup & Email Verification ─────────────────────────────────────────────


def signup(payload: SignupRequest, db: Session) -> tuple[str, str]:
    """
    Create a new user and generate an email-verification token.
    Returns (user_email, raw_verification_token) for the caller to email.
    """
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken. Please choose another.",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()

    raw_token = secrets.token_urlsafe(32)
    db.add(
        OneTimeToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            purpose=TokenPurpose.EMAIL_VERIFICATION,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=_EMAIL_TOKEN_EXPIRE_HOURS),
        )
    )
    db.commit()
    logger.info("New account registered: user_id=%s, role=%s", user.id, user.role.value)
    return user.email, raw_token


def verify_email(token: str, db: Session) -> None:
    """Verify user email with one-time token."""
    otp = (
        db.query(OneTimeToken)
        .filter(
            OneTimeToken.token_hash == _hash_token(token),
            OneTimeToken.purpose == TokenPurpose.EMAIL_VERIFICATION,
            OneTimeToken.is_used.is_(False),
            OneTimeToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )
    otp.is_used = True
    otp.user.is_verified = True
    db.commit()
    logger.info("Email verified: user_id=%s", otp.user_id)


def resend_verification(email: str, db: Session) -> tuple[str, str] | None:
    """
    Invalidate any pending verification tokens and issue a fresh one.
    Returns (email, raw_token) or None if the account doesn't need verification.
    """
    user: User | None = (
        db.query(User)
        .filter(User.email == email, User.is_verified.is_(False), User.is_active.is_(True))
        .first()
    )
    if not user:
        return None

    db.query(OneTimeToken).filter(
        OneTimeToken.user_id == user.id,
        OneTimeToken.purpose == TokenPurpose.EMAIL_VERIFICATION,
        OneTimeToken.is_used.is_(False),
    ).update({"is_used": True})

    raw_token = secrets.token_urlsafe(32)
    db.add(
        OneTimeToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            purpose=TokenPurpose.EMAIL_VERIFICATION,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=_EMAIL_TOKEN_EXPIRE_HOURS),
        )
    )
    db.commit()
    return user.email, raw_token


# ─── Login & 2FA ─────────────────────────────────────────────────────────────


def login(payload: LoginRequest, db: Session) -> dict[str, Any]:
    """
    Authenticate a user.

    Returns one of:
      {"status": "success",      "access_token": str, "refresh_token": str}
      {"status": "otp_required", "pending_token": str, "email": str, "otp": str}

    The "otp" key in the otp_required result is returned to the API layer ONLY
    to pass to the background email task - it is never logged or stored raw.
    """
    user: User | None = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    now = datetime.now(timezone.utc)
    if user.is_locked and user.locked_until:
        # Handle timezone-aware and naive datetime comparison (SQLite stores naive)
        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > now:
            logger.warning("Login attempt on locked account: user_id=%s", user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked until {locked_until.strftime('%Y-%m-%d %H:%M UTC')}.",
            )

    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= _MAX_FAILED_ATTEMPTS:
            user.is_locked = True
            user.locked_until = now + timedelta(minutes=_LOCK_DURATION_MINUTES)
            logger.warning("Account locked after failed attempts: user_id=%s", user.id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    # Password is correct - reset brute-force counters immediately
    user.failed_login_attempts = 0
    user.is_locked = False
    user.locked_until = None
    db.commit()

    # Email must be verified before issuing tokens
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in.",
        )

    # ── 2FA path ──────────────────────────────────────────────────────────────
    if user.is_2fa_enabled:
        # Invalidate any previous OTP for this user (one active OTP at a time)
        db.query(OTPCode).filter(OTPCode.user_id == user.id).delete()

        raw_otp = _generate_otp()
        db.add(
            OTPCode(
                user_id=user.id,
                otp_hash=_hash_token(raw_otp),
                expires_at=now + timedelta(minutes=_OTP_EXPIRE_MINUTES),
            )
        )
        pending_token = create_2fa_pending_token(str(user.id))
        db.commit()

        logger.info("2FA OTP generated: user_id=%s", user.id)
        return {
            "status": "otp_required",
            "pending_token": pending_token,
            "email": user.email,
            "otp": raw_otp,
        }

    # ── Direct login path ─────────────────────────────────────────────────────
    access_token, raw_refresh = _create_session(user.id, now, db)
    logger.info("Successful login: user_id=%s, role=%s", user.id, user.role.value)
    return {"status": "success", "access_token": access_token, "refresh_token": raw_refresh}


def verify_otp(pending_token: str, otp: str, db: Session) -> tuple[str, str]:
    """Validate 2FA OTP and issue a full session on success."""
    from jose import JWTError

    try:
        payload = decode_2fa_pending_token(pending_token)
        user_id: str = payload["sub"]
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )

    otp_record: OTPCode | None = (
        db.query(OTPCode)
        .filter(
            OTPCode.user_id == user_id,
            OTPCode.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OTPCode.created_at.desc())
        .first()
    )
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP.",
        )

    if otp_record.attempt_count >= _MAX_OTP_ATTEMPTS:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please log in and request a new OTP.",
        )

    if not _verify_otp_hash(otp, otp_record.otp_hash):
        otp_record.attempt_count += 1
        db.commit()
        remaining = _MAX_OTP_ATTEMPTS - otp_record.attempt_count
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid OTP. {remaining} attempt(s) remaining.",
        )

    # OTP is correct - consume it immediately (single-use)
    db.delete(otp_record)

    user: User | None = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    now = datetime.now(timezone.utc)
    access_token, raw_refresh = _create_session(user.id, now, db)
    logger.info("2FA verified, session created: user_id=%s", user_id)
    return access_token, raw_refresh


# ─── Token Rotation ───────────────────────────────────────────────────────────


def refresh_access_token(refresh_token: str, db: Session) -> tuple[str, str]:
    """
    Refresh token rotation - the old token is revoked and a brand-new pair is issued.
    Prevents replay attacks: a stolen refresh token becomes invalid as soon as the
    legitimate client rotates it.
    """
    old_session: UserSession | None = (
        db.query(UserSession)
        .filter(
            UserSession.refresh_token_hash == _hash_token(refresh_token),
            UserSession.is_revoked.is_(False),
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not old_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    # Revoke the old session
    old_session.is_revoked = True

    # Issue a fresh pair
    now = datetime.now(timezone.utc)
    access_token, raw_refresh = _create_session(old_session.user_id, now, db)
    return access_token, raw_refresh


# ─── Logout ───────────────────────────────────────────────────────────────────


def logout(refresh_token: str, db: Session) -> None:
    """Revoke the refresh token (invalidate session)."""
    session: UserSession | None = (
        db.query(UserSession)
        .filter(UserSession.refresh_token_hash == _hash_token(refresh_token))
        .first()
    )
    if session and not session.is_revoked:
        session.is_revoked = True
        db.commit()


# ─── Password Reset ───────────────────────────────────────────────────────────


def forgot_password(email: str, db: Session) -> tuple[str, str] | None:
    """
    Generate a password-reset token.
    Returns (email, raw_token) or None if no account was found.
    Always returns silently to the caller - never reveal if an email exists.
    """
    user: User | None = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    raw_token = secrets.token_urlsafe(32)
    db.add(
        OneTimeToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            purpose=TokenPurpose.PASSWORD_RESET,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=_RESET_TOKEN_EXPIRE_HOURS),
        )
    )
    db.commit()
    return user.email, raw_token


def reset_password(payload: ResetPasswordRequest, db: Session) -> None:
    """Reset password using a valid one-time token."""
    otp: OneTimeToken | None = (
        db.query(OneTimeToken)
        .filter(
            OneTimeToken.token_hash == _hash_token(payload.token),
            OneTimeToken.purpose == TokenPurpose.PASSWORD_RESET,
            OneTimeToken.is_used.is_(False),
            OneTimeToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    otp.is_used = True
    otp.user.hashed_password = hash_password(payload.password)

    # Revoke ALL active sessions - forces re-authentication everywhere
    db.query(UserSession).filter(UserSession.user_id == otp.user_id).update({"is_revoked": True})
    db.commit()
    logger.info("Password reset: user_id=%s", otp.user_id)


# ─── Internal ─────────────────────────────────────────────────────────────────


def _create_session(user_id: Any, now: datetime, db: Session) -> tuple[str, str]:
    """Create a new UserSession row and return (access_token, raw_refresh_token)."""
    access_token = create_access_token(str(user_id))
    raw_refresh = create_refresh_token()
    db.add(
        UserSession(
            user_id=user_id,
            refresh_token_hash=_hash_token(raw_refresh),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    db.commit()
    return access_token, raw_refresh
