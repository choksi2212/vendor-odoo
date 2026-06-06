"""Activity logs API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.activity_log import ActivityLog
from app.models.user import User, UserRole

router = APIRouter()


@router.get("")
def list_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    action: Optional[str] = Query(None, description="Filter by action"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER)
    ),
    db: Session = Depends(get_db),
):
    """
    List activity logs with filters.
    Admin only - full audit trail access.
    """
    query = db.query(ActivityLog)

    if entity_type:
        query = query.filter(ActivityLog.entity_type == entity_type.upper())
    if action:
        query = query.filter(ActivityLog.action == action.upper())
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)

    total = query.count()
    logs = (
        query
        .order_by(ActivityLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for log in logs:
        items.append({
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}
