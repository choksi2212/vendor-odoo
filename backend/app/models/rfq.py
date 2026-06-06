import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from app.db.base import GUID, generate_uuid
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID, generate_uuid


class RFQStatus(str, PyEnum):
    """RFQ lifecycle status."""
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class RFQVendorStatus(str, PyEnum):
    """Status of vendor invitation to RFQ."""
    INVITED = "invited"
    VIEWED = "viewed"
    SUBMITTED = "submitted"


class RFQ(Base):
    """Request for Quotation."""
    __tablename__ = "rfqs"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)
    deadline = Column(Date, nullable=False)
    status = Column(
        Enum(RFQStatus), 
        nullable=False, 
        default=RFQStatus.DRAFT,
        index=True
    )
    
    # Audit fields
    created_by = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    vendor_associations = relationship("RFQVendor", back_populates="rfq", cascade="all, delete-orphan")
    attachments = relationship("RFQAttachment", back_populates="rfq", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="rfq", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="rfq")

    __table_args__ = (
        Index("ix_rfqs_created_by", "created_by"),
        Index("ix_rfqs_deadline", "deadline"),
    )


class RFQVendor(Base):
    """Junction table for RFQ-Vendor many-to-many relationship."""
    __tablename__ = "rfq_vendors"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    rfq_id = Column(
        GUID,
        ForeignKey("rfqs.id", ondelete="CASCADE"),
        nullable=False,
    )
    vendor_id = Column(
        GUID,
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(
        Enum(RFQVendorStatus), 
        nullable=False, 
        default=RFQVendorStatus.INVITED
    )
    invited_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="vendor_associations")
    vendor = relationship("Vendor", back_populates="rfq_associations")

    __table_args__ = (
        Index("ix_rfq_vendors_rfq_id", "rfq_id"),
        Index("ix_rfq_vendors_vendor_id", "vendor_id"),
    )


class RFQAttachment(Base):
    """File attachments for RFQs."""
    __tablename__ = "rfq_attachments"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    rfq_id = Column(
        GUID,
        ForeignKey("rfqs.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="attachments")

    __table_args__ = (Index("ix_rfq_attachments_rfq_id", "rfq_id"),)


