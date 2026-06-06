"""Authentication request/response schemas with robust input validation."""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.user import UserRole

_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)"
    r"(?=.*[@$!%*?&#^()_\-+=\[\]{}|\\:;\"'<>,.?/~`])"
    r"[A-Za-z\d@$!%*?&#^()_\-+=\[\]{}|\\:;\"'<>,.?/~`]{8,128}$"
)

_PASSWORD_RULES = (
    "Password must be 8-128 characters and contain at least one uppercase letter, "
    "one lowercase letter, one digit, and one special character."
)

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


def _normalize_email(v: str) -> str:
    return v.lower().strip()


def _validate_password(v: str) -> str:
    if not _PASSWORD_RE.match(v):
        raise ValueError(_PASSWORD_RULES)
    return v


# ─── Request Models ──────────────────────────────────────────────────────────


class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str
    confirm_password: str
    role: UserRole = Field(
        description="User role: procurement_officer, vendor, manager, admin"
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_email(v)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not _USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3-30 characters and contain only letters, numbers, or underscores."
            )
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: UserRole) -> UserRole:
        valid_roles = [r.value for r in UserRole]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "SignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_email(v)


class VerifyEmailRequest(BaseModel):
    token: str


class EmailRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_email(v)


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return _validate_password(v)

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyOTPRequest(BaseModel):
    pending_token: str
    otp: str = Field(pattern=r"^\d{6}$", description="Exactly 6 digits")


# ─── Response Models ──────────────────────────────────────────────────────────


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OTPPendingResponse(BaseModel):
    """Returned when 2FA is enabled and OTP is sent to email."""
    message: str = "OTP sent to your email. It expires in 5 minutes."
    requires_otp: bool = True
    pending_token: str


class MessageResponse(BaseModel):
    message: str
