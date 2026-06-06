import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, func
from app.db.base import GUID, generate_uuid
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID, generate_uuid


class InvoiceStatus(str, PyEnum):
    """Invoice status."""
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    CANCELLED = "cancelled"


class Invoice(Base):
    """Invoice generated from Purchase Order."""
    __tablename__ = "invoices"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)  # INV-YYYY-XXXX
    purchase_order_id = Column(
        GUID,
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    vendor_id = Column(
        GUID,
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
    )
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    status = Column(
        Enum(InvoiceStatus), 
        nullable=False, 
        default=InvoiceStatus.DRAFT,
        index=True
    )
    pdf_path = Column(String(500), nullable=True)  # Path to generated PDF
    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    generated_by = Column(
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
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    vendor = relationship("Vendor")
    generator = relationship("User", foreign_keys=[generated_by])
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_invoices_purchase_order_id", "purchase_order_id"),
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_generated_by", "generated_by"),
    )


class InvoiceLineItem(Base):
    """Line items in an Invoice."""
    __tablename__ = "invoice_line_items"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    invoice_id = Column(
        GUID,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")

    __table_args__ = (Index("ix_invoice_line_items_invoice_id", "invoice_id"),)


