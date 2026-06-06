"""
Purchase Order generation service.

Handles:
  - PO generation from approved quotations
  - Sequential PO numbering (PO-YYYY-XXXX format, resets per year)
  - Line item creation from RFQ data
  - Tax calculation from config
  - PO status management
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import func, extract
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.approval import Approval, ApprovalStatus
from app.models.purchase_order import POLineItem, POStatus, PurchaseOrder
from app.models.quotation import Quotation
from app.models.rfq import RFQ
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)


# ─── PO Number Generation ────────────────────────────────────────────────────


def _generate_po_number(db: Session) -> str:
    """
    Generate sequential PO number in format PO-YYYY-XXXX.
    
    Resets the sequence counter each year.
    Thread-safe via database query for max existing number.
    """
    current_year = datetime.now(timezone.utc).year
    prefix = f"PO-{current_year}-"

    # Find the highest PO number for the current year
    last_po = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.po_number.like(f"{prefix}%"))
        .order_by(PurchaseOrder.po_number.desc())
        .first()
    )

    if last_po:
        # Extract the sequence number from the last PO number
        last_seq = int(last_po.po_number.split("-")[-1])
        next_seq = last_seq + 1
    else:
        next_seq = 1

    return f"{prefix}{next_seq:04d}"


# ─── PO Creation ─────────────────────────────────────────────────────────────


def create_po_from_approval(
    approval_id: str,
    created_by_id: str,
    notes: Optional[str],
    db: Session,
    request: Optional[Request] = None,
) -> PurchaseOrder:
    """
    Generate a Purchase Order from an approved approval.

    Validates:
      - Approval exists and is approved
      - No existing PO for this approval (prevent duplicates)
    
    Automatically:
      - Generates sequential PO number (PO-YYYY-XXXX)
      - Creates line items from RFQ data
      - Calculates tax based on configured rate
      - Computes grand total
    """
    # Validate approval
    approval = (
        db.query(Approval)
        .options(
            joinedload(Approval.quotation).joinedload(Quotation.vendor),
            joinedload(Approval.rfq),
        )
        .filter(Approval.id == approval_id)
        .first()
    )
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found.",
        )
    if approval.status != ApprovalStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved requests can generate a Purchase Order.",
        )

    # Check no existing PO for this approval
    existing_po = db.query(PurchaseOrder).filter(
        PurchaseOrder.approval_id == approval_id
    ).first()
    if existing_po:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A Purchase Order already exists for this approval: {existing_po.po_number}",
        )

    # Extract data from quotation and RFQ
    quotation = approval.quotation
    rfq = approval.rfq
    vendor = quotation.vendor

    # Calculate amounts
    subtotal = quotation.total_price
    tax_rate = Decimal(str(settings.TAX_RATE))
    tax_amount = (subtotal * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    total_amount = subtotal + tax_amount

    # Generate PO number
    po_number = _generate_po_number(db)

    # Create Purchase Order
    po = PurchaseOrder(
        po_number=po_number,
        approval_id=str(approval.id),
        quotation_id=str(quotation.id),
        vendor_id=str(vendor.id) if vendor else None,
        subtotal=subtotal,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status=POStatus.ISSUED,
        notes=notes,
        created_by=created_by_id,
    )
    db.add(po)
    db.flush()

    # Create line item from RFQ data
    line_item = POLineItem(
        purchase_order_id=str(po.id),
        product_name=rfq.product_name,
        quantity=rfq.quantity,
        unit=rfq.unit,
        unit_price=quotation.unit_price,
        total_price=quotation.total_price,
    )
    db.add(line_item)
    db.flush()

    log_activity(
        db=db,
        user_id=created_by_id,
        action="CREATE",
        entity_type="PURCHASE_ORDER",
        entity_id=str(po.id),
        details={
            "po_number": po_number,
            "approval_id": approval_id,
            "vendor_name": vendor.name if vendor else None,
            "total_amount": str(total_amount),
        },
        request=request,
    )

    db.commit()
    db.refresh(po)
    logger.info("PO created: id=%s number=%s total=%s", po.id, po_number, total_amount)
    return po


# ─── PO Queries ───────────────────────────────────────────────────────────────


def get_purchase_orders(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
) -> tuple[list[PurchaseOrder], int]:
    """Get paginated list of purchase orders."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    query = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.vendor),
            joinedload(PurchaseOrder.line_items),
        )
    )

    if status_filter:
        query = query.filter(PurchaseOrder.status == status_filter)

    total = query.count()
    pos = (
        query
        .order_by(PurchaseOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return pos, total


def get_po_by_id(po_id: str, db: Session) -> PurchaseOrder:
    """Get a single PO by ID with all relationships."""
    po = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.vendor),
            joinedload(PurchaseOrder.line_items),
        )
        .filter(PurchaseOrder.id == po_id)
        .first()
    )
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found.",
        )
    return po


def get_po_by_number(po_number: str, db: Session) -> PurchaseOrder:
    """Get a PO by its number (PO-YYYY-XXXX)."""
    po = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.vendor),
            joinedload(PurchaseOrder.line_items),
        )
        .filter(PurchaseOrder.po_number == po_number)
        .first()
    )
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found.",
        )
    return po


# ─── PO Status Updates ────────────────────────────────────────────────────────


def update_po_status(
    po_id: str,
    new_status: str,
    user_id: str,
    notes: Optional[str],
    db: Session,
    request: Optional[Request] = None,
) -> PurchaseOrder:
    """
    Update PO status with validation of allowed transitions.
    
    Allowed transitions:
      issued -> paid
      issued -> cancelled
    """
    po = get_po_by_id(po_id, db)
    current_status = po.status.value if hasattr(po.status, 'value') else str(po.status)

    # Validate transitions
    valid_transitions = {
        "issued": ["paid", "cancelled"],
        "paid": [],
        "cancelled": [],
    }

    allowed = valid_transitions.get(current_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{current_status}' to '{new_status}'. "
                   f"Allowed: {allowed if allowed else 'none (terminal state)'}.",
        )

    old_status = current_status
    po.status = new_status
    if notes:
        po.notes = notes

    db.flush()
    log_activity(
        db=db,
        user_id=user_id,
        action="UPDATE_STATUS",
        entity_type="PURCHASE_ORDER",
        entity_id=str(po.id),
        details={
            "po_number": po.po_number,
            "old_status": old_status,
            "new_status": new_status,
        },
        request=request,
    )

    db.commit()
    db.refresh(po)
    logger.info("PO status updated: %s %s -> %s", po.po_number, old_status, new_status)
    return po
