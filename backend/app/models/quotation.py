import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, Numeric, Text, func
from app.db.base import GUID, generate_uuid
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID, generate_uuid


class QuotationStatus(str, PyEnum):
    """Quotation lifecycle status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    SELECTED = "selected"
    REJECTED = "rejected"


class Quotation(Base):
    """Vendor quotation for an RFQ."""
    __tablename__ = "quotations"

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
    unit_price = Column(Numeric(15, 2), nullable=False)  # Price per unit
    total_price = Column(Numeric(15, 2), nullable=False)  # unit_price * quantity
    delivery_days = Column(Integer, nullable=False)  # Number of days for delivery
    notes = Column(Text, nullable=True)  # Additional comments from vendor
    status = Column(
        Enum(QuotationStatus), 
        nullable=False, 
        default=QuotationStatus.DRAFT,
        index=True
    )
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    rfq = relationship("RFQ", back_populates="quotations")
    vendor = relationship("Vendor", back_populates="quotations")
    approvals = relationship("Approval", back_populates="quotation")
    purchase_orders = relationship("PurchaseOrder", back_populates="quotation")

    __table_args__ = (
        Index("ix_quotations_rfq_id", "rfq_id"),
        Index("ix_quotations_vendor_id", "vendor_id"),
    )


