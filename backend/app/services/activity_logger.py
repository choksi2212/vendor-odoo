"""
Activity logging service for complete audit trail.

Logs all user actions in the system for accountability and compliance.
Every create, update, delete operation should be logged.
"""

import logging
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog

logger = logging.getLogger(__name__)


def log_activity(
    db: Session,
    user_id: Optional[str],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> ActivityLog:
    """
    Create an activity log entry.

    Args:
        db: Database session
        user_id: ID of the user performing the action
        action: Action performed (e.g., "CREATE", "UPDATE", "DELETE")
        entity_type: Type of entity affected (e.g., "VENDOR", "RFQ")
        entity_id: ID of the affected entity
        details: Additional context (stored as JSONB)
        request: FastAPI request object for IP/user-agent extraction

    Returns:
        The created ActivityLog record
    """
    ip_address = None
    user_agent = None

    if request:
        # Extract client IP (handles proxied requests)
        ip_address = request.client.host if request.client else None
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        user_agent = request.headers.get("user-agent", "")[:500]

    log_entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log_entry)
    # Do not commit here - let the caller manage the transaction
    db.flush()

    logger.info(
        "Activity logged: user=%s action=%s entity=%s/%s",
        user_id, action, entity_type, entity_id,
    )
    return log_entry
