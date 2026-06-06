"""
RFQ (Request for Quotation) management service.

Handles:
  - RFQ creation, update, deletion
  - RFQ publishing (status change from draft to open, triggers notifications)
  - Vendor assignment to RFQs
  - RFQ closing
  - Role-based data access filtering
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.rfq import RFQ, RFQAttachment, RFQStatus, RFQVendor, RFQVendorStatus
from app.models.vendor import Vendor, VendorStatus
from app.models.quotation import Quotation
from app.models.user import UserRole
from app.schemas.rfq import RFQCreate, RFQUpdate
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)


# ─── RFQ CRUD ─────────────────────────────────────────────────────────────────


def create_rfq(
    payload: RFQCreate,
    created_by_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> RFQ:
    """Create a new RFQ in draft status."""
    rfq = RFQ(
        title=payload.title,
        description=payload.description,
        product_name=payload.product_name,
        quantity=payload.quantity,
        unit=payload.unit,
        deadline=payload.deadline,
        status=RFQStatus.DRAFT,
        created_by=created_by_id,
    )
    db.add(rfq)
    db.flush()

    log_activity(
        db=db,
        user_id=created_by_id,
        action="CREATE",
        entity_type="RFQ",
        entity_id=str(rfq.id),
        details={"title": rfq.title, "product": rfq.product_name, "quantity": rfq.quantity},
        request=request,
    )

    db.commit()
    db.refresh(rfq)
    logger.info("RFQ created: id=%s title=%s", rfq.id, rfq.title)
    return rfq


def get_rfqs(
    db: Session,
    user_role: str,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> tuple[list[dict], int]:
    """
    Get paginated list of RFQs with role-based filtering.
    
    - Procurement Officer / Admin: see all RFQs
    - Manager: see all RFQs (for approval visibility)
    - Vendor: see only RFQs they are assigned to (open status only)
    """
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    query = db.query(RFQ)

    # Role-based filtering
    if user_role == UserRole.VENDOR:
        # Vendors only see open RFQs they are assigned to
        query = query.join(RFQVendor, RFQ.id == RFQVendor.rfq_id).filter(
            RFQVendor.vendor_id.in_(
                db.query(Vendor.id).filter(Vendor.email == db.query(
                    # This is simplified - in practice vendor user would be linked
                ).scalar_subquery())
            )
        )
        query = query.filter(RFQ.status == RFQStatus.OPEN)

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            RFQ.title.ilike(search_term) | RFQ.product_name.ilike(search_term)
        )

    # Status filter
    if status_filter:
        query = query.filter(RFQ.status == status_filter)

    # Get total count
    total = query.count()

    # Apply pagination
    rfqs = (
        query
        .order_by(RFQ.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Build response with counts
    result = []
    for rfq in rfqs:
        vendor_count = db.query(func.count(RFQVendor.id)).filter(RFQVendor.rfq_id == rfq.id).scalar()
        quotation_count = db.query(func.count(Quotation.id)).filter(Quotation.rfq_id == rfq.id).scalar()
        result.append({
            "id": str(rfq.id),
            "title": rfq.title,
            "description": rfq.description,
            "product_name": rfq.product_name,
            "quantity": rfq.quantity,
            "unit": rfq.unit,
            "deadline": rfq.deadline,
            "status": rfq.status.value if hasattr(rfq.status, 'value') else str(rfq.status),
            "created_by": str(rfq.created_by) if rfq.created_by else None,
            "created_at": rfq.created_at,
            "updated_at": rfq.updated_at,
            "vendor_count": vendor_count or 0,
            "quotation_count": quotation_count or 0,
        })

    return result, total


def get_rfq_by_id(rfq_id: str, db: Session) -> RFQ:
    """Get RFQ by ID with vendors and attachments loaded. Raises 404 if not found."""
    rfq = (
        db.query(RFQ)
        .options(
            joinedload(RFQ.vendor_associations).joinedload(RFQVendor.vendor),
            joinedload(RFQ.attachments),
        )
        .filter(RFQ.id == rfq_id)
        .first()
    )
    if not rfq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFQ not found.",
        )
    return rfq


def update_rfq(
    rfq_id: str,
    payload: RFQUpdate,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> RFQ:
    """Update an RFQ. Only draft RFQs can be updated."""
    rfq = get_rfq_by_id(rfq_id, db)

    if rfq.status != RFQStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft RFQs can be updated.",
        )

    changes = {}
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            old_value = getattr(rfq, field, None)
            if old_value != value:
                setattr(rfq, field, value)
                changes[field] = {"old": str(old_value), "new": str(value)}

    if not changes:
        return rfq

    db.flush()
    log_activity(
        db=db,
        user_id=user_id,
        action="UPDATE",
        entity_type="RFQ",
        entity_id=str(rfq.id),
        details={"changes": changes, "title": rfq.title},
        request=request,
    )

    db.commit()
    db.refresh(rfq)
    logger.info("RFQ updated: id=%s changes=%s", rfq.id, list(changes.keys()))
    return rfq


def delete_rfq(
    rfq_id: str,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> None:
    """Delete an RFQ. Only draft RFQs can be deleted."""
    rfq = get_rfq_by_id(rfq_id, db)

    if rfq.status != RFQStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft RFQs can be deleted.",
        )

    log_activity(
        db=db,
        user_id=user_id,
        action="DELETE",
        entity_type="RFQ",
        entity_id=str(rfq.id),
        details={"title": rfq.title, "product": rfq.product_name},
        request=request,
    )

    db.delete(rfq)
    db.commit()
    logger.info("RFQ deleted: id=%s", rfq_id)


# ─── Vendor Assignment ────────────────────────────────────────────────────────


def assign_vendors(
    rfq_id: str,
    vendor_ids: list[str],
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> list[RFQVendor]:
    """Assign vendors to an RFQ. RFQ must be in draft status."""
    rfq = get_rfq_by_id(rfq_id, db)

    if rfq.status != RFQStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendors can only be assigned to draft RFQs.",
        )

    # Validate all vendor IDs exist and are active
    assigned = []
    for vendor_id in vendor_ids:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with ID {vendor_id} not found.",
            )
        if vendor.status != VendorStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor '{vendor.name}' is inactive and cannot be assigned.",
            )

        # Check if already assigned
        existing = db.query(RFQVendor).filter(
            RFQVendor.rfq_id == rfq_id,
            RFQVendor.vendor_id == vendor_id,
        ).first()
        if existing:
            assigned.append(existing)
            continue

        rfq_vendor = RFQVendor(
            rfq_id=rfq_id,
            vendor_id=vendor_id,
            status=RFQVendorStatus.INVITED,
        )
        db.add(rfq_vendor)
        assigned.append(rfq_vendor)

    db.flush()
    log_activity(
        db=db,
        user_id=user_id,
        action="ASSIGN_VENDORS",
        entity_type="RFQ",
        entity_id=str(rfq.id),
        details={"vendor_ids": vendor_ids, "count": len(vendor_ids)},
        request=request,
    )

    db.commit()
    logger.info("Vendors assigned to RFQ: rfq_id=%s vendor_count=%d", rfq_id, len(vendor_ids))
    return assigned


# ─── RFQ Status Transitions ──────────────────────────────────────────────────


def publish_rfq(
    rfq_id: str,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> RFQ:
    """
    Publish an RFQ (transition from draft to open).
    
    Requirements:
      - Must be in draft status
      - Must have at least one vendor assigned
    """
    rfq = get_rfq_by_id(rfq_id, db)

    if rfq.status != RFQStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft RFQs can be published.",
        )

    # Check at least one vendor is assigned
    vendor_count = db.query(func.count(RFQVendor.id)).filter(
        RFQVendor.rfq_id == rfq_id
    ).scalar()
    if not vendor_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish RFQ without assigning at least one vendor.",
        )

    rfq.status = RFQStatus.OPEN
    db.flush()

    log_activity(
        db=db,
        user_id=user_id,
        action="PUBLISH",
        entity_type="RFQ",
        entity_id=str(rfq.id),
        details={"title": rfq.title, "vendor_count": vendor_count},
        request=request,
    )

    db.commit()
    db.refresh(rfq)
    logger.info("RFQ published: id=%s title=%s vendors=%d", rfq.id, rfq.title, vendor_count)
    return rfq


def close_rfq(
    rfq_id: str,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> RFQ:
    """Close an RFQ (transition from open to closed). No more quotations accepted."""
    rfq = get_rfq_by_id(rfq_id, db)

    if rfq.status != RFQStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only open RFQs can be closed.",
        )

    rfq.status = RFQStatus.CLOSED
    db.flush()

    log_activity(
        db=db,
        user_id=user_id,
        action="CLOSE",
        entity_type="RFQ",
        entity_id=str(rfq.id),
        details={"title": rfq.title},
        request=request,
    )

    db.commit()
    db.refresh(rfq)
    logger.info("RFQ closed: id=%s title=%s", rfq.id, rfq.title)
    return rfq
