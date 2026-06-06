"""Purchase Order request/response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ─── Request Schemas ──────────────────────────────────────────────────────────


class POCreate(BaseModel):
    """Request to manually create a PO from an approved quotation/approval."""
    approval_id: str = Field(description="Approved approval UUID")
    notes: Optional[str] = Field(None, max_length=2000)


class POStatusUpdate(BaseModel):
    """Request to update PO status."""
    status: str = Field(description="New status: issued, paid, cancelled")
    notes: Optional[str] = Field(None, max_length=2000)

    from pydantic import field_validator

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = ("issued", "paid", "cancelled")
        if v not in valid:
            raise ValueError(f"Status must be one of: {', '.join(valid)}")
        return v


# ─── Response Schemas ─────────────────────────────────────────────────────────


class POLineItemResponse(BaseModel):
    """PO line item response."""
    id: str
    product_name: str
    quantity: int
    unit: str
    unit_price: Decimal
    total_price: Decimal

    model_config = {"from_attributes": True}


class POResponse(BaseModel):
    """Full Purchase Order response."""
    id: str
    po_number: str
    approval_id: Optional[str]
    quotation_id: Optional[str]
    vendor_id: Optional[str]
    vendor_name: Optional[str] = None
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    line_items: list[POLineItemResponse] = []

    model_config = {"from_attributes": True}


class POListResponse(BaseModel):
    """Paginated PO list."""
    items: list[POResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
