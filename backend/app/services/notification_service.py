"""
Notification service for creating and delivering notifications.

Creates database notifications and optionally pushes them
via WebSocket for real-time delivery.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> Notification:
    """
    Create a notification in the database.
    
    The WebSocket push is handled separately by the caller if needed,
    since DB operations are synchronous but WS push is async.

    Args:
        db: Database session
        user_id: Target user UUID
        title: Short notification title
        message: Full notification message
        notification_type: INFO, WARNING, ERROR, SUCCESS
        entity_type: Related entity type (e.g., "RFQ", "APPROVAL")
        entity_id: Related entity UUID

    Returns:
        Created Notification object
    """
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(notification)
    db.flush()

    logger.info(
        "Notification created: user=%s title=%s type=%s",
        user_id, title, notification_type.value,
    )
    return notification


def get_notification_payload(notification: Notification) -> dict:
    """
    Convert a Notification to a WebSocket-friendly payload.
    
    Use this to push via ws_manager.send_to_user() after commit.
    """
    return {
        "type": "notification",
        "data": {
            "id": str(notification.id),
            "notification_type": notification.type.value if hasattr(notification.type, 'value') else str(notification.type),
            "title": notification.title,
            "message": notification.message,
            "entity_type": notification.entity_type,
            "entity_id": str(notification.entity_id) if notification.entity_id else None,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
        },
    }
