import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Text, func
from app.db.base import GUID, generate_uuid
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID, generate_uuid


class ApprovalStatus(str, PyEnum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Approval(Base):
    """Approval request for quotation."""
    __tablename__ = "approvals"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    rfq_id = Column(
        GUID,
        ForeignKey("rfqs.id", ondelete="CASCADE"),
        nullable=False,
    )
    quotation_id = Column(
        GUID,
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
    )
    requested_by = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(
        Enum(ApprovalStatus), 
        nullable=False, 
        default=ApprovalStatus.PENDING,
        index=True
    )
    remarks = Column(Text, nullable=True)  # Comments from approver
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rfq = relationship("RFQ", back_populates="approvals")
    quotation = relationship("Quotation", back_populates="approvals")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    history = relationship("ApprovalHistory", back_populates="approval", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="approval")

    __table_args__ = (
        Index("ix_approvals_rfq_id", "rfq_id"),
        Index("ix_approvals_quotation_id", "quotation_id"),
        Index("ix_approvals_requested_by", "requested_by"),
        Index("ix_approvals_approved_by", "approved_by"),
    )


class ApprovalHistory(Base):
    """History of approval status changes."""
    __tablename__ = "approval_history"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    approval_id = Column(
        GUID,
        ForeignKey("approvals.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(Enum(ApprovalStatus), nullable=False)
    remarks = Column(Text, nullable=True)
    changed_by = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    approval = relationship("Approval", back_populates="history")
    changer = relationship("User", foreign_keys=[changed_by])

    __table_args__ = (
        Index("ix_approval_history_approval_id", "approval_id"),
    )


