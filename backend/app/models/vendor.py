import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from app.db.base import GUID, generate_uuid
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID, generate_uuid


class VendorStatus(str, PyEnum):
    """Vendor account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class VendorCategory(Base):
    """Categories for vendor classification."""
    __tablename__ = "vendor_categories"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    vendors = relationship("Vendor", back_populates="category")


class Vendor(Base):
    """Vendor master table."""
    __tablename__ = "vendors"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    category_id = Column(
        GUID,
        ForeignKey("vendor_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    gst_number = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    status = Column(
        Enum(VendorStatus), 
        nullable=False, 
        default=VendorStatus.ACTIVE,
        index=True
    )
    rating = Column(Numeric(2, 1), nullable=True)  # 0.0 to 5.0
    
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
    category = relationship("VendorCategory", back_populates="vendors")
    creator = relationship("User", foreign_keys=[created_by])
    rfq_associations = relationship("RFQVendor", back_populates="vendor")
    quotations = relationship("Quotation", back_populates="vendor")

    __table_args__ = (
        Index("ix_vendors_category_id", "category_id"),
        Index("ix_vendors_created_by", "created_by"),
    )


