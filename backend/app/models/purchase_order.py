import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, func
from app.db.base import GUID, generate_uuid
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID, generate_uuid


class POStatus(str, PyEnum):
    """Purchase Order status."""
    ISSUED = "issued"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    """Purchase Order generated from approved quotation."""
    __tablename__ = "purchase_orders"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    po_number = Column(String(50), unique=True, nullable=False, index=True)  # PO-YYYY-XXXX
    approval_id = Column(
        GUID,
        ForeignKey("approvals.id", ondelete="SET NULL"),
        nullable=True,
    )
    quotation_id = Column(
        GUID,
        ForeignKey("quotations.id", ondelete="SET NULL"),
        nullable=True,
    )
    vendor_id = Column(
        GUID,
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
    )
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False)  # Tax percentage (e.g., 18.00)
    tax_amount = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    status = Column(
        Enum(POStatus), 
        nullable=False, 
        default=POStatus.ISSUED,
        index=True
    )
    notes = Column(Text, nullable=True)
    
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
    approval = relationship("Approval", back_populates="purchase_orders")
    quotation = relationship("Quotation", back_populates="purchase_orders")
    vendor = relationship("Vendor")
    creator = relationship("User", foreign_keys=[created_by])
    line_items = relationship("POLineItem", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order")

    __table_args__ = (
        Index("ix_purchase_orders_approval_id", "approval_id"),
        Index("ix_purchase_orders_quotation_id", "quotation_id"),
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_created_by", "created_by"),
    )


class POLineItem(Base):
    """Line items in a Purchase Order."""
    __tablename__ = "po_line_items"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    purchase_order_id = Column(
        GUID,
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")

    __table_args__ = (Index("ix_po_line_items_purchase_order_id", "purchase_order_id"),)


