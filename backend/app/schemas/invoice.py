"""Invoice request/response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── Request Schemas ──────────────────────────────────────────────────────────


class InvoiceCreate(BaseModel):
    """Request to create an invoice from a Purchase Order."""
    purchase_order_id: str = Field(description="Purchase Order UUID")
    notes: Optional[str] = Field(None, max_length=2000, description="Payment terms or notes")


class InvoiceStatusUpdate(BaseModel):
    """Request to mark invoice as paid."""
    pass  # No additional fields needed for mark-paid


# ─── Response Schemas ─────────────────────────────────────────────────────────


class InvoiceLineItemResponse(BaseModel):
    """Invoice line item."""
    id: str
    product_name: str
    quantity: int
    unit: str
    unit_price: Decimal
    total_price: Decimal

    model_config = {"from_attributes": True}


class InvoiceResponse(BaseModel):
    """Full invoice response."""
    id: str
    invoice_number: str
    purchase_order_id: Optional[str]
    po_number: Optional[str] = None
    vendor_id: Optional[str]
    vendor_name: Optional[str] = None
    vendor_email: Optional[str] = None
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    pdf_path: Optional[str]
    notes: Optional[str]
    paid_at: Optional[datetime]
    generated_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    line_items: list[InvoiceLineItemResponse] = []

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Paginated invoice list."""
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
