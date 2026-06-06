from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/2fa/enable", response_model=MessageResponse)
def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.is_2fa_enabled = True
    db.commit()
    return {"message": "Two-factor authentication enabled. Your next login will require an OTP."}


@router.post("/2fa/disable", response_model=MessageResponse)
def disable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.is_2fa_enabled = False
    db.commit()
    return {"message": "Two-factor authentication disabled."}
