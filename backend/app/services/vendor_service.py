"""
Vendor management service - all business logic for vendor CRUD operations.

Handles:
  - Vendor creation with GST validation
  - Vendor listing with pagination, filtering, and search
  - Vendor updates and status changes
  - Vendor category management
  - Activity logging for all operations
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.vendor import Vendor, VendorCategory, VendorStatus
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorCategoryCreate
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)


# ─── Vendor Category Operations ──────────────────────────────────────────────


def create_category(
    payload: VendorCategoryCreate,
    db: Session,
) -> VendorCategory:
    """Create a new vendor category."""
    existing = db.query(VendorCategory).filter(
        VendorCategory.name == payload.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{payload.name}' already exists.",
        )

    category = VendorCategory(
        name=payload.name,
        description=payload.description,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    logger.info("Vendor category created: id=%s name=%s", category.id, category.name)
    return category


def get_categories(db: Session) -> list[VendorCategory]:
    """Get all vendor categories ordered by name."""
    return db.query(VendorCategory).order_by(VendorCategory.name).all()


# ─── Vendor CRUD Operations ──────────────────────────────────────────────────


def create_vendor(
    payload: VendorCreate,
    created_by_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> Vendor:
    """
    Create a new vendor.
    
    Validates:
      - GST number is unique
      - Category exists (if provided)
    """
    # Check GST uniqueness
    existing = db.query(Vendor).filter(Vendor.gst_number == payload.gst_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A vendor with this GST number already exists.",
        )

    # Validate category if provided
    if payload.category_id:
        category = db.query(VendorCategory).filter(
            VendorCategory.id == payload.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor category not found.",
            )

    vendor = Vendor(
        name=payload.name,
        gst_number=payload.gst_number,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        category_id=payload.category_id if payload.category_id else None,
        created_by=created_by_id,
        status=VendorStatus.ACTIVE,
    )
    db.add(vendor)
    db.flush()

    # Log activity
    log_activity(
        db=db,
        user_id=created_by_id,
        action="CREATE",
        entity_type="VENDOR",
        entity_id=str(vendor.id),
        details={
            "vendor_name": vendor.name,
            "gst_number": vendor.gst_number,
            "email": vendor.email,
        },
        request=request,
    )

    db.commit()
    db.refresh(vendor)
    logger.info("Vendor created: id=%s name=%s gst=%s", vendor.id, vendor.name, vendor.gst_number)
    return vendor


def get_vendors(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    category_id: Optional[str] = None,
) -> tuple[list[Vendor], int]:
    """
    Get paginated list of vendors with optional filtering.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        search: Search term (matches name, email, gst_number)
        status_filter: Filter by status ("active" or "inactive")
        category_id: Filter by category UUID

    Returns:
        Tuple of (vendors list, total count)
    """
    # Enforce bounds
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    query = db.query(Vendor).options(joinedload(Vendor.category))

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Vendor.name.ilike(search_term),
                Vendor.email.ilike(search_term),
                Vendor.gst_number.ilike(search_term),
            )
        )

    # Apply status filter
    if status_filter:
        query = query.filter(Vendor.status == status_filter)

    # Apply category filter
    if category_id:
        query = query.filter(Vendor.category_id == category_id)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    vendors = (
        query
        .order_by(Vendor.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return vendors, total


def get_vendor_by_id(vendor_id: str, db: Session) -> Vendor:
    """Get a single vendor by ID. Raises 404 if not found."""
    vendor = (
        db.query(Vendor)
        .options(joinedload(Vendor.category))
        .filter(Vendor.id == vendor_id)
        .first()
    )
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found.",
        )
    return vendor


def update_vendor(
    vendor_id: str,
    payload: VendorUpdate,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> Vendor:
    """
    Update vendor details. Only provided (non-None) fields are updated.
    """
    vendor = get_vendor_by_id(vendor_id, db)

    changes = {}
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            old_value = getattr(vendor, field, None)
            if old_value != value:
                # Validate category if being changed
                if field == "category_id":
                    category = db.query(VendorCategory).filter(
                        VendorCategory.id == value
                    ).first()
                    if not category:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Vendor category not found.",
                        )

                setattr(vendor, field, value)
                changes[field] = {"old": str(old_value), "new": str(value)}

    if not changes:
        return vendor

    db.flush()

    # Log activity
    log_activity(
        db=db,
        user_id=user_id,
        action="UPDATE",
        entity_type="VENDOR",
        entity_id=str(vendor.id),
        details={"changes": changes, "vendor_name": vendor.name},
        request=request,
    )

    db.commit()
    db.refresh(vendor)
    logger.info("Vendor updated: id=%s changes=%s", vendor.id, list(changes.keys()))
    return vendor


def deactivate_vendor(
    vendor_id: str,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> None:
    """
    Deactivate (soft delete) a vendor.
    Does not delete the record - sets status to inactive.
    """
    vendor = get_vendor_by_id(vendor_id, db)

    if vendor.status == VendorStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor is already inactive.",
        )

    vendor.status = VendorStatus.INACTIVE
    db.flush()

    # Log activity
    log_activity(
        db=db,
        user_id=user_id,
        action="DEACTIVATE",
        entity_type="VENDOR",
        entity_id=str(vendor.id),
        details={"vendor_name": vendor.name, "gst_number": vendor.gst_number},
        request=request,
    )

    db.commit()
    logger.info("Vendor deactivated: id=%s name=%s", vendor.id, vendor.name)
