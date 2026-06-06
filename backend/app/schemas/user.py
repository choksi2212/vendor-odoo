"""User response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Public user profile response."""
    id: UUID
    email: EmailStr
    username: str | None
    role: str
    is_verified: bool
    is_active: bool
    is_2fa_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBriefResponse(BaseModel):
    """Minimal user info for embedding in other responses."""
    id: UUID
    email: EmailStr
    username: str | None
    role: str

    model_config = {"from_attributes": True}
