import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, func, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID, generate_uuid


class ActivityLog(Base):
    """Audit trail of all user actions in the system."""
    __tablename__ = "activity_logs"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action = Column(String(100), nullable=False, index=True)  # e.g., "CREATE", "UPDATE", "DELETE"
    entity_type = Column(String(100), nullable=False, index=True)  # e.g., "RFQ", "VENDOR", "INVOICE"
    entity_id = Column(GUID, nullable=True, index=True)  # ID of the affected entity
    details = Column(JSON, nullable=True)  # Additional context (stored as JSON)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("ix_activity_logs_user_id", "user_id"),
        Index("ix_activity_logs_created_at", "created_at"),
        Index("ix_activity_logs_entity_type_id", "entity_type", "entity_id"),
    )


