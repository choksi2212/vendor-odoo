"""Approval workflow request/response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ─── Request Schemas ──────────────────────────────────────────────────────────


class ApprovalCreate(BaseModel):
    """Request to create an approval request."""
    rfq_id: str = Field(description="RFQ UUID")
    quotation_id: str = Field(description="Selected quotation UUID to approve")


class ApprovalDecision(BaseModel):
    """Request to approve or reject."""
    remarks: Optional[str] = Field(None, max_length=2000, description="Decision remarks")


# ─── Response Schemas ─────────────────────────────────────────────────────────


class ApprovalHistoryItem(BaseModel):
    """Single entry in the approval timeline."""
    id: str
    status: str
    remarks: Optional[str]
    changed_by: Optional[str]
    changed_by_name: Optional[str] = None
    changed_at: datetime

    model_config = {"from_attributes": True}


class ApprovalResponse(BaseModel):
    """Full approval response."""
    id: str
    rfq_id: str
    rfq_title: Optional[str] = None
    quotation_id: str
    vendor_name: Optional[str] = None
    total_amount: Optional[Decimal] = None
    requested_by: Optional[str]
    requested_by_name: Optional[str] = None
    approved_by: Optional[str]
    approved_by_name: Optional[str] = None
    status: str
    remarks: Optional[str]
    requested_at: datetime
    reviewed_at: Optional[datetime]
    history: list[ApprovalHistoryItem] = []

    model_config = {"from_attributes": True}


class ApprovalListResponse(BaseModel):
    """Paginated approval list."""
    items: list[ApprovalResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
