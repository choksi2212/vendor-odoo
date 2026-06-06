"""Quotation request/response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── Request Schemas ──────────────────────────────────────────────────────────


class QuotationCreate(BaseModel):
    """Request to create/submit a quotation for an RFQ."""
    rfq_id: str = Field(description="RFQ UUID to submit quotation for")
    vendor_id: str = Field(description="Vendor UUID submitting the quotation")
    unit_price: Decimal = Field(gt=0, max_digits=15, decimal_places=2, description="Price per unit")
    delivery_days: int = Field(gt=0, le=365, description="Delivery time in days")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")


class QuotationUpdate(BaseModel):
    """Request to update a draft quotation."""
    unit_price: Optional[Decimal] = Field(None, gt=0, max_digits=15, decimal_places=2)
    delivery_days: Optional[int] = Field(None, gt=0, le=365)
    notes: Optional[str] = Field(None, max_length=2000)


# ─── Response Schemas ─────────────────────────────────────────────────────────


class QuotationResponse(BaseModel):
    """Quotation response."""
    id: str
    rfq_id: str
    vendor_id: str
    vendor_name: Optional[str] = None
    unit_price: Decimal
    total_price: Decimal
    delivery_days: int
    notes: Optional[str]
    status: str
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuotationComparisonItem(BaseModel):
    """Single quotation in a comparison view."""
    id: str
    vendor_id: str
    vendor_name: str
    vendor_email: str
    vendor_rating: Optional[float] = None
    unit_price: Decimal
    total_price: Decimal
    delivery_days: int
    notes: Optional[str]
    is_lowest_price: bool = False
    is_fastest_delivery: bool = False


class QuotationComparison(BaseModel):
    """Side-by-side quotation comparison for an RFQ."""
    rfq_id: str
    rfq_title: str
    product_name: str
    quantity: int
    unit: str
    total_quotations: int
    lowest_price: Decimal
    highest_price: Decimal
    average_price: Decimal
    fastest_delivery: int
    slowest_delivery: int
    average_delivery: float
    quotations: list[QuotationComparisonItem]
