"""Notification management API endpoints."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.auth import MessageResponse

router = APIRouter()


class NotificationResponse(dict):
    pass


@router.get("/my")
def get_my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notifications for the current user."""
    query = db.query(Notification).filter(Notification.user_id == str(current_user.id))

    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    total = query.count()
    notifications = (
        query
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for n in notifications:
        items.append({
            "id": str(n.id),
            "type": n.type.value if hasattr(n.type, 'value') else str(n.type),
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "entity_type": n.entity_type,
            "entity_id": str(n.entity_id) if n.entity_id else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "read_at": n.read_at.isoformat() if n.read_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/{notification_id}/read", response_model=MessageResponse)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == str(current_user.id),
    ).first()

    if not notification:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Notification marked as read."}


@router.put("/mark-all-read", response_model=MessageResponse)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for current user."""
    now = datetime.now(timezone.utc)
    db.query(Notification).filter(
        Notification.user_id == str(current_user.id),
        Notification.is_read.is_(False),
    ).update({"is_read": True, "read_at": now})
    db.commit()
    return {"message": "All notifications marked as read."}
