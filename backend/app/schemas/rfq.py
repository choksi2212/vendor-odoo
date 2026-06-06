"""RFQ (Request for Quotation) request/response schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── RFQ Schemas ──────────────────────────────────────────────────────────────


class RFQCreate(BaseModel):
    """Request to create a new RFQ."""
    title: str = Field(min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    product_name: str = Field(min_length=2, max_length=255)
    quantity: int = Field(gt=0, description="Quantity must be positive")
    unit: str = Field(min_length=1, max_length=50, description="Unit of measure (e.g., pieces, kg, units)")
    deadline: date = Field(description="Submission deadline (YYYY-MM-DD)")

    @field_validator("title", "product_name", "unit")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator("deadline")
    @classmethod
    def deadline_must_be_future(cls, v: date) -> date:
        if v <= date.today():
            raise ValueError("Deadline must be a future date.")
        return v


class RFQUpdate(BaseModel):
    """Request to update an RFQ. All fields optional."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    product_name: Optional[str] = Field(None, min_length=2, max_length=255)
    quantity: Optional[int] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    deadline: Optional[date] = None

    @field_validator("deadline")
    @classmethod
    def deadline_must_be_future(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v <= date.today():
            raise ValueError("Deadline must be a future date.")
        return v


class RFQVendorAssign(BaseModel):
    """Request to assign vendors to an RFQ."""
    vendor_ids: list[str] = Field(min_length=1, description="List of vendor UUIDs to assign")


# ─── Response Schemas ─────────────────────────────────────────────────────────


class RFQAttachmentResponse(BaseModel):
    """RFQ file attachment response."""
    id: str
    file_name: str
    file_size: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class RFQVendorResponse(BaseModel):
    """Vendor assignment to an RFQ."""
    id: str
    vendor_id: str
    vendor_name: Optional[str] = None
    vendor_email: Optional[str] = None
    status: str
    invited_at: datetime

    model_config = {"from_attributes": True}


class RFQResponse(BaseModel):
    """Full RFQ response."""
    id: str
    title: str
    description: Optional[str]
    product_name: str
    quantity: int
    unit: str
    deadline: date
    status: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    vendor_count: int = 0
    quotation_count: int = 0

    model_config = {"from_attributes": True}


class RFQDetailResponse(RFQResponse):
    """Detailed RFQ response with vendors and attachments."""
    vendors: list[RFQVendorResponse] = []
    attachments: list[RFQAttachmentResponse] = []


class RFQListResponse(BaseModel):
    """Paginated RFQ list response."""
    items: list[RFQResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
