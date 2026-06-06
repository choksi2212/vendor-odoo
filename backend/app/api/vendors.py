"""Vendor management API endpoints."""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.vendor import (
    VendorCategoryCreate,
    VendorCategoryResponse,
    VendorCreate,
    VendorListResponse,
    VendorResponse,
    VendorUpdate,
)
from app.services import vendor_service

router = APIRouter()


# ─── Vendor Category Endpoints ────────────────────────────────────────────────


@router.get("/categories", response_model=list[VendorCategoryResponse])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all vendor categories. Accessible by all authenticated users."""
    categories = vendor_service.get_categories(db)
    return categories


@router.post("/categories", response_model=VendorCategoryResponse, status_code=201)
def create_category(
    payload: VendorCategoryCreate,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)
    ),
    db: Session = Depends(get_db),
):
    """Create a new vendor category. Admin and Procurement Officer only."""
    category = vendor_service.create_category(payload, db)
    return category


# ─── Vendor CRUD Endpoints ────────────────────────────────────────────────────


@router.get("", response_model=VendorListResponse)
def list_vendors(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, max_length=100, description="Search by name, email, or GST"),
    status: Optional[str] = Query(None, description="Filter by status: active/inactive"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """
    List vendors with pagination, search, and filters.
    Accessible by Procurement Officer, Manager, and Admin.
    """
    vendors, total = vendor_service.get_vendors(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status,
        category_id=category_id,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return VendorListResponse(
        items=vendors,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=VendorResponse, status_code=201)
def create_vendor(
    payload: VendorCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Create a new vendor. Procurement Officer and Admin only."""
    vendor = vendor_service.create_vendor(
        payload=payload,
        created_by_id=str(current_user.id),
        db=db,
        request=request,
    )
    return vendor


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: str,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Get a single vendor by ID."""
    vendor = vendor_service.get_vendor_by_id(vendor_id, db)
    return vendor


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: str,
    payload: VendorUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Update vendor details. Procurement Officer and Admin only."""
    vendor = vendor_service.update_vendor(
        vendor_id=vendor_id,
        payload=payload,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return vendor


@router.delete("/{vendor_id}", status_code=204)
def deactivate_vendor(
    vendor_id: str,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)
    ),
    db: Session = Depends(get_db),
):
    """Deactivate (soft delete) a vendor. Admin and Procurement Officer only."""
    vendor_service.deactivate_vendor(
        vendor_id=vendor_id,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return None
