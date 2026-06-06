"""
Invoice management service.

Handles:
  - Invoice creation from Purchase Orders
  - Sequential invoice numbering (INV-YYYY-XXXX)
  - PDF generation and storage
  - Invoice status management (draft -> issued -> paid)
  - Email delivery with PDF attachment
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.purchase_order import POStatus, PurchaseOrder
from app.services import pdf_service
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)


# ─── Invoice Number Generation ────────────────────────────────────────────────


def _generate_invoice_number(db: Session) -> str:
    """
    Generate sequential invoice number in format INV-YYYY-XXXX.
    Resets the sequence counter each year.
    """
    current_year = datetime.now(timezone.utc).year
    prefix = f"INV-{current_year}-"

    last_invoice = (
        db.query(Invoice)
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .order_by(Invoice.invoice_number.desc())
        .first()
    )

    if last_invoice:
        last_seq = int(last_invoice.invoice_number.split("-")[-1])
        next_seq = last_seq + 1
    else:
        next_seq = 1

    return f"{prefix}{next_seq:04d}"


# ─── Invoice Creation ─────────────────────────────────────────────────────────


def create_invoice_from_po(
    purchase_order_id: str,
    generated_by_id: str,
    notes: Optional[str],
    db: Session,
    request: Optional[Request] = None,
) -> Invoice:
    """
    Create an invoice from a Purchase Order.

    Validates:
      - PO exists and is in 'issued' status
      - No existing invoice for this PO (prevent duplicates)

    Automatically:
      - Generates sequential invoice number
      - Copies line items from PO
      - Copies amounts (subtotal, tax, total)
      - Sets status to 'draft'
    """
    # Validate PO
    po = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.vendor),
            joinedload(PurchaseOrder.line_items),
        )
        .filter(PurchaseOrder.id == purchase_order_id)
        .first()
    )
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found.",
        )

    po_status = po.status.value if hasattr(po.status, 'value') else str(po.status)
    if po_status not in ("issued", "paid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoices can only be created for issued or paid Purchase Orders.",
        )

    # Check for existing invoice
    existing = db.query(Invoice).filter(
        Invoice.purchase_order_id == purchase_order_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An invoice already exists for this PO: {existing.invoice_number}",
        )

    # Generate invoice number
    invoice_number = _generate_invoice_number(db)

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        purchase_order_id=str(po.id),
        vendor_id=str(po.vendor_id) if po.vendor_id else None,
        subtotal=po.subtotal,
        tax_rate=po.tax_rate,
        tax_amount=po.tax_amount,
        total_amount=po.total_amount,
        status=InvoiceStatus.DRAFT,
        notes=notes,
        generated_by=generated_by_id,
    )
    db.add(invoice)
    db.flush()

    # Copy line items from PO
    for po_item in po.line_items:
        line_item = InvoiceLineItem(
            invoice_id=str(invoice.id),
            product_name=po_item.product_name,
            quantity=po_item.quantity,
            unit=po_item.unit,
            unit_price=po_item.unit_price,
            total_price=po_item.total_price,
        )
        db.add(line_item)

    db.flush()

    log_activity(
        db=db,
        user_id=generated_by_id,
        action="CREATE",
        entity_type="INVOICE",
        entity_id=str(invoice.id),
        details={
            "invoice_number": invoice_number,
            "po_number": po.po_number,
            "total_amount": str(po.total_amount),
        },
        request=request,
    )

    db.commit()
    db.refresh(invoice)
    logger.info("Invoice created: id=%s number=%s po=%s", invoice.id, invoice_number, po.po_number)
    return invoice


# ─── Invoice Queries ──────────────────────────────────────────────────────────


def get_invoices(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
) -> tuple[list[Invoice], int]:
    """Get paginated list of invoices."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    query = (
        db.query(Invoice)
        .options(
            joinedload(Invoice.vendor),
            joinedload(Invoice.purchase_order),
            joinedload(Invoice.line_items),
        )
    )

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    total = query.count()
    invoices = (
        query
        .order_by(Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return invoices, total


def get_invoice_by_id(invoice_id: str, db: Session) -> Invoice:
    """Get a single invoice by ID with all relationships."""
    invoice = (
        db.query(Invoice)
        .options(
            joinedload(Invoice.vendor),
            joinedload(Invoice.purchase_order),
            joinedload(Invoice.line_items),
        )
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )
    return invoice


# ─── PDF Generation ───────────────────────────────────────────────────────────


def generate_pdf(
    invoice_id: str,
    db: Session,
) -> bytes:
    """
    Generate PDF for an invoice and save to disk.
    Returns PDF bytes for download.
    """
    invoice = get_invoice_by_id(invoice_id, db)

    # Build line items data
    line_items = []
    for li in invoice.line_items:
        line_items.append({
            "product_name": li.product_name,
            "quantity": li.quantity,
            "unit": li.unit,
            "unit_price": li.unit_price,
            "total_price": li.total_price,
        })

    # Generate PDF
    pdf_bytes = pdf_service.generate_invoice_pdf(
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.created_at or datetime.now(timezone.utc),
        vendor_name=invoice.vendor.name if invoice.vendor else "Unknown Vendor",
        vendor_email=invoice.vendor.email if invoice.vendor else "",
        vendor_address=invoice.vendor.address if invoice.vendor else None,
        vendor_gst=invoice.vendor.gst_number if invoice.vendor else None,
        line_items=line_items,
        subtotal=invoice.subtotal,
        tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        notes=invoice.notes,
        po_number=invoice.purchase_order.po_number if invoice.purchase_order else None,
    )

    # Save to disk
    filepath = pdf_service.save_invoice_pdf(invoice.invoice_number, pdf_bytes)
    invoice.pdf_path = filepath
    db.commit()

    return pdf_bytes


# ─── Status Management ────────────────────────────────────────────────────────


def mark_invoice_issued(
    invoice_id: str,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> Invoice:
    """Mark invoice as issued (draft -> issued)."""
    invoice = get_invoice_by_id(invoice_id, db)

    current = invoice.status.value if hasattr(invoice.status, 'value') else str(invoice.status)
    if current != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft invoices can be marked as issued.",
        )

    invoice.status = InvoiceStatus.ISSUED
    db.flush()

    log_activity(
        db=db,
        user_id=user_id,
        action="ISSUE",
        entity_type="INVOICE",
        entity_id=str(invoice.id),
        details={"invoice_number": invoice.invoice_number},
        request=request,
    )

    db.commit()
    db.refresh(invoice)
    return invoice


def mark_invoice_paid(
    invoice_id: str,
    user_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> Invoice:
    """Mark invoice as paid (issued -> paid). Updates PO status too."""
    invoice = get_invoice_by_id(invoice_id, db)

    current = invoice.status.value if hasattr(invoice.status, 'value') else str(invoice.status)
    if current != "issued":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only issued invoices can be marked as paid.",
        )

    now = datetime.now(timezone.utc)
    invoice.status = InvoiceStatus.PAID
    invoice.paid_at = now

    # Update PO status to paid
    if invoice.purchase_order:
        invoice.purchase_order.status = POStatus.PAID

    db.flush()

    log_activity(
        db=db,
        user_id=user_id,
        action="MARK_PAID",
        entity_type="INVOICE",
        entity_id=str(invoice.id),
        details={
            "invoice_number": invoice.invoice_number,
            "paid_at": now.isoformat(),
        },
        request=request,
    )

    db.commit()
    db.refresh(invoice)
    logger.info("Invoice marked paid: %s", invoice.invoice_number)
    return invoice
