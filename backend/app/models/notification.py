import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, String, Text, func
from app.db.base import GUID, generate_uuid
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID, generate_uuid


class NotificationType(str, PyEnum):
    """Types of notifications."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class Notification(Base):
    """User notifications."""
    __tablename__ = "notifications"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(
        Enum(NotificationType), 
        nullable=False, 
        default=NotificationType.INFO
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)  # e.g., "RFQ", "QUOTATION"
    entity_id = Column(GUID, nullable=True)  # Link to related entity
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_created_at", "created_at"),
    )


