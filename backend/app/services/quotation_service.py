"""
Quotation management service.

Handles:
  - Quotation creation by vendors
  - Quotation updates (draft only)
  - Quotation submission (locks the quotation)
  - Side-by-side comparison with analytics
  - Quotation selection (winner marking)
"""

import logging
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.models.quotation import Quotation, QuotationStatus
from app.models.rfq import RFQ, RFQStatus, RFQVendor
from app.models.vendor import Vendor
from app.schemas.quotation import QuotationCreate, QuotationUpdate
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)


# ─── Quotation CRUD ───────────────────────────────────────────────────────────


def create_quotation(
    payload: QuotationCreate,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> Quotation:
    """
    Create a new quotation for an RFQ.

    Validates:
      - RFQ exists and is open
      - Vendor exists and is assigned to the RFQ
      - Vendor hasn't already submitted a quotation for this RFQ
    """
    # Validate RFQ exists and is open
    rfq = db.query(RFQ).filter(RFQ.id == payload.rfq_id).first()
    if not rfq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFQ not found.",
        )
    if rfq.status != RFQStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quotations can only be submitted for open RFQs.",
        )

    # Validate vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == payload.vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found.",
        )

    # Validate vendor is assigned to this RFQ
    assignment = db.query(RFQVendor).filter(
        RFQVendor.rfq_id == payload.rfq_id,
        RFQVendor.vendor_id == payload.vendor_id,
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor is not assigned to this RFQ.",
        )

    # Check for existing quotation
    existing = db.query(Quotation).filter(
        Quotation.rfq_id == payload.rfq_id,
        Quotation.vendor_id == payload.vendor_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vendor has already submitted a quotation for this RFQ.",
        )

    # Calculate total price
    total_price = payload.unit_price * rfq.quantity

    quotation = Quotation(
        rfq_id=payload.rfq_id,
        vendor_id=payload.vendor_id,
        unit_price=payload.unit_price,
        total_price=total_price,
        delivery_days=payload.delivery_days,
        notes=payload.notes,
        status=QuotationStatus.DRAFT,
    )
    db.add(quotation)
    db.flush()

    log_activity(
        db=db,
        user_id=user_id,
        action="CREATE",
        entity_type="QUOTATION",
        entity_id=str(quotation.id),
        details={
            "rfq_id": str(payload.rfq_id),
            "vendor_id": str(payload.vendor_id),
            "unit_price": str(payload.unit_price),
            "total_price": str(total_price),
        },
        request=request,
    )

    db.commit()
    db.refresh(quotation)
    logger.info(
        "Quotation created: id=%s rfq=%s vendor=%s",
        quotation.id, payload.rfq_id, payload.vendor_id,
    )
    return quotation


def get_quotation_by_id(quotation_id: str, db: Session) -> Quotation:
    """Get a single quotation by ID. Raises 404 if not found."""
    quotation = (
        db.query(Quotation)
        .options(joinedload(Quotation.vendor), joinedload(Quotation.rfq))
        .filter(Quotation.id == quotation_id)
        .first()
    )
    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotation not found.",
        )
    return quotation


def get_quotations_for_rfq(rfq_id: str, db: Session) -> list[Quotation]:
    """Get all quotations for an RFQ."""
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFQ not found.",
        )
    return (
        db.query(Quotation)
        .options(joinedload(Quotation.vendor))
        .filter(Quotation.rfq_id == rfq_id)
        .order_by(Quotation.total_price.asc())
        .all()
    )


def update_quotation(
    quotation_id: str,
    payload: QuotationUpdate,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> Quotation:
    """Update a draft quotation. Only draft quotations can be modified."""
    quotation = get_quotation_by_id(quotation_id, db)

    if quotation.status != QuotationStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft quotations can be updated.",
        )

    changes = {}
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            old_value = getattr(quotation, field, None)
            if old_value != value:
                setattr(quotation, field, value)
                changes[field] = {"old": str(old_value), "new": str(value)}

    # Recalculate total if unit_price changed
    if "unit_price" in changes:
        rfq = quotation.rfq
        quotation.total_price = quotation.unit_price * rfq.quantity
        changes["total_price"] = {"old": str(changes.get("unit_price", {}).get("old")), "new": str(quotation.total_price)}

    if not changes:
        return quotation

    db.flush()
    log_activity(
        db=db,
        user_id=user_id,
        action="UPDATE",
        entity_type="QUOTATION",
        entity_id=str(quotation.id),
        details={"changes": changes},
        request=request,
    )

    db.commit()
    db.refresh(quotation)
    return quotation


def submit_quotation(
    quotation_id: str,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> Quotation:
    """
    Submit a quotation (lock it for review).
    
    Once submitted:
      - Cannot be modified
      - Visible to procurement officer for comparison
      - Updates RFQVendor status to 'submitted'
    """
    quotation = get_quotation_by_id(quotation_id, db)

    if quotation.status != QuotationStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft quotations can be submitted.",
        )

    # Verify RFQ is still open
    if quotation.rfq.status != RFQStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit quotation - RFQ is no longer open.",
        )

    from datetime import datetime, timezone
    quotation.status = QuotationStatus.SUBMITTED
    quotation.submitted_at = datetime.now(timezone.utc)

    # Update vendor assignment status
    rfq_vendor = db.query(RFQVendor).filter(
        RFQVendor.rfq_id == quotation.rfq_id,
        RFQVendor.vendor_id == quotation.vendor_id,
    ).first()
    if rfq_vendor:
        from app.models.rfq import RFQVendorStatus
        rfq_vendor.status = RFQVendorStatus.SUBMITTED

    db.flush()
    log_activity(
        db=db,
        user_id=user_id,
        action="SUBMIT",
        entity_type="QUOTATION",
        entity_id=str(quotation.id),
        details={
            "rfq_id": str(quotation.rfq_id),
            "vendor_id": str(quotation.vendor_id),
            "total_price": str(quotation.total_price),
        },
        request=request,
    )

    db.commit()
    db.refresh(quotation)
    logger.info("Quotation submitted: id=%s rfq=%s", quotation.id, quotation.rfq_id)
    return quotation


# ─── Comparison ───────────────────────────────────────────────────────────────


def compare_quotations(rfq_id: str, db: Session) -> dict:
    """
    Generate side-by-side comparison of all submitted quotations for an RFQ.

    Returns comparison data with:
      - Min/max/average price
      - Min/max/average delivery time
      - Flags for lowest price and fastest delivery
    """
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFQ not found.",
        )

    quotations = (
        db.query(Quotation)
        .options(joinedload(Quotation.vendor))
        .filter(
            Quotation.rfq_id == rfq_id,
            Quotation.status == QuotationStatus.SUBMITTED,
        )
        .all()
    )

    if not quotations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No submitted quotations available for comparison.",
        )

    # Calculate analytics
    prices = [q.total_price for q in quotations]
    deliveries = [q.delivery_days for q in quotations]

    lowest_price = min(prices)
    highest_price = max(prices)
    average_price = sum(prices) / len(prices)
    fastest_delivery = min(deliveries)
    slowest_delivery = max(deliveries)
    average_delivery = sum(deliveries) / len(deliveries)

    # Build comparison items
    items = []
    for q in quotations:
        items.append({
            "id": str(q.id),
            "vendor_id": str(q.vendor_id),
            "vendor_name": q.vendor.name if q.vendor else "Unknown",
            "vendor_email": q.vendor.email if q.vendor else "",
            "vendor_rating": float(q.vendor.rating) if q.vendor and q.vendor.rating else None,
            "unit_price": q.unit_price,
            "total_price": q.total_price,
            "delivery_days": q.delivery_days,
            "notes": q.notes,
            "is_lowest_price": q.total_price == lowest_price,
            "is_fastest_delivery": q.delivery_days == fastest_delivery,
        })

    return {
        "rfq_id": str(rfq.id),
        "rfq_title": rfq.title,
        "product_name": rfq.product_name,
        "quantity": rfq.quantity,
        "unit": rfq.unit,
        "total_quotations": len(quotations),
        "lowest_price": lowest_price,
        "highest_price": highest_price,
        "average_price": round(average_price, 2),
        "fastest_delivery": fastest_delivery,
        "slowest_delivery": slowest_delivery,
        "average_delivery": round(average_delivery, 1),
        "quotations": items,
    }
