"""User profile management endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user


@router.post("/2fa/enable", response_model=MessageResponse)
def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enable two-factor authentication for current user."""
    current_user.is_2fa_enabled = True
    db.commit()
    return {"message": "Two-factor authentication enabled. Your next login will require an OTP."}


@router.post("/2fa/disable", response_model=MessageResponse)
def disable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable two-factor authentication for current user."""
    current_user.is_2fa_enabled = False
    db.commit()
    return {"message": "Two-factor authentication disabled."}


@router.get("/me/vendor-profile")
def get_vendor_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get vendor profile for vendor users.
    Returns vendor entity linked by email matching.
    """
    from app.models.vendor import Vendor
    from app.models.user import UserRole
    
    if current_user.role != UserRole.VENDOR:
        return {
            "is_vendor_user": False,
            "has_vendor_entity": False,
            "message": "Not a vendor user"
        }
    
    vendor = db.query(Vendor).filter(Vendor.email == current_user.email).first()
    
    if vendor:
        return {
            "is_vendor_user": True,
            "has_vendor_entity": True,
            "vendor_id": str(vendor.id),
            "vendor_name": vendor.name,
            "vendor_email": vendor.email,
            "vendor_status": vendor.status.value if hasattr(vendor.status, 'value') else str(vendor.status),
            "message": "Vendor profile linked successfully"
        }
    else:
        return {
            "is_vendor_user": True,
            "has_vendor_entity": False,
            "user_email": current_user.email,
            "message": f"No vendor entity found with email {current_user.email}. Please contact admin to create a vendor profile with this email.",
        }

