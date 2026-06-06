from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.core import email as email_service
from app.core.security import limiter
from app.db.session import get_db
from app.schemas.auth import (
    EmailRequest,
    LoginRequest,
    MessageResponse,
    OTPPendingResponse,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    VerifyEmailRequest,
    VerifyOTPRequest,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=MessageResponse, status_code=201)
def signup(payload: SignupRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    user_email, raw_token = auth_service.signup(payload, db)
    bg.add_task(email_service.send_verification_email, user_email, raw_token)
    return {"message": "Account created. Please check your email to verify your address."}


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    auth_service.verify_email(payload.token, db)
    return {"message": "Email verified successfully. You can now sign in."}


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit("3/hour")
def resend_verification(request: Request, payload: EmailRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    result = auth_service.resend_verification(payload.email, db)
    if result:
        user_email, raw_token = result
        bg.add_task(email_service.send_verification_email, user_email, raw_token)
    return {"message": "If your email is unverified, a new verification link has been sent."}


@router.post("/login", response_model=TokenResponse | OTPPendingResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    result = auth_service.login(payload, db)
    if result["status"] == "otp_required":
        bg.add_task(email_service.send_otp_email, result["email"], result["otp"])
        return OTPPendingResponse(pending_token=result["pending_token"])
    return TokenResponse(access_token=result["access_token"], refresh_token=result["refresh_token"])


@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit("10/minute")
def verify_otp(request: Request, payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    access_token, refresh_token = auth_service.verify_otp(payload.pending_token, payload.otp, db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh token rotation — issues a new access + refresh token pair; old token is revoked."""
    access_token, refresh_token = auth_service.refresh_access_token(payload.refresh_token, db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    auth_service.logout(payload.refresh_token, db)
    return {"message": "Logged out successfully."}


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/hour")
def forgot_password(request: Request, payload: EmailRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    result = auth_service.forgot_password(payload.email, db)
    if result:
        user_email, raw_token = result
        bg.add_task(email_service.send_reset_email, user_email, raw_token)
    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password(payload, db)
    return {"message": "Password reset successfully. Please sign in with your new password."}
