from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str | None
    is_verified: bool
    is_active: bool
    is_2fa_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
