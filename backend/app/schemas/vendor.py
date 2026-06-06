"""Vendor management request/response schemas with robust validation."""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# Indian GST Number format: 2 digits state code + 10 char PAN + 1 entity code + Z + 1 checksum
_GST_PATTERN = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$")


# ─── Vendor Category Schemas ─────────────────────────────────────────────────


class VendorCategoryCreate(BaseModel):
    """Request to create a vendor category."""
    name: str = Field(min_length=2, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class VendorCategoryResponse(BaseModel):
    """Vendor category response."""
    id: str
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Vendor Schemas ───────────────────────────────────────────────────────────


class VendorCreate(BaseModel):
    """Request to create a new vendor."""
    name: str = Field(min_length=2, max_length=255, description="Vendor company name")
    gst_number: str = Field(min_length=15, max_length=15, description="Indian GST number (15 chars)")
    email: EmailStr = Field(description="Vendor contact email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=1000, description="Full address")
    category_id: Optional[str] = Field(None, description="Category UUID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("gst_number")
    @classmethod
    def validate_gst_number(cls, v: str) -> str:
        v = v.strip().upper()
        if not _GST_PATTERN.match(v):
            raise ValueError(
                "Invalid GST number format. Must be 15 characters: "
                "2 digit state code + 10 char PAN + entity code + Z + checksum."
            )
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            # Allow +, digits, hyphens, spaces, parentheses
            cleaned = re.sub(r"[\s\-\(\)\+]", "", v)
            if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError("Phone number must contain 7-15 digits.")
        return v


class VendorUpdate(BaseModel):
    """Request to update vendor details. All fields optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[str] = None
    status: Optional[str] = None  # "active" or "inactive"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("active", "inactive"):
            raise ValueError("Status must be 'active' or 'inactive'.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            cleaned = re.sub(r"[\s\-\(\)\+]", "", v)
            if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError("Phone number must contain 7-15 digits.")
        return v


class VendorResponse(BaseModel):
    """Full vendor response."""
    id: str
    name: str
    gst_number: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    status: str
    rating: Optional[float]
    category_id: Optional[str]
    category: Optional[VendorCategoryResponse] = None
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VendorListResponse(BaseModel):
    """Paginated vendor list response."""
    items: list[VendorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
