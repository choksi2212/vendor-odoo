"""Invoice management API endpoints."""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceLineItemResponse,
    InvoiceListResponse,
    InvoiceResponse,
)
from app.services import invoice_service

router = APIRouter()


@router.get("", response_model=InvoiceListResponse)
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter: draft, issued, paid, cancelled"),
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """List invoices with pagination and status filter."""
    invoices, total = invoice_service.get_invoices(
        db=db, page=page, page_size=page_size, status_filter=status,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return InvoiceListResponse(
        items=[_build_response(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    payload: InvoiceCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Create an invoice from a Purchase Order."""
    invoice = invoice_service.create_invoice_from_po(
        purchase_order_id=payload.purchase_order_id,
        generated_by_id=str(current_user.id),
        notes=payload.notes,
        db=db,
        request=request,
    )
    return _build_response(invoice)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: str,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Get invoice details."""
    invoice = invoice_service.get_invoice_by_id(invoice_id, db)
    return _build_response(invoice)


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: str,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Generate and download invoice PDF."""
    pdf_bytes = invoice_service.generate_pdf(invoice_id, db)
    invoice = invoice_service.get_invoice_by_id(invoice_id, db)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={invoice.invoice_number}.pdf"
        },
    )


@router.post("/{invoice_id}/issue", response_model=InvoiceResponse)
def issue_invoice(
    invoice_id: str,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Mark invoice as issued (draft -> issued)."""
    invoice = invoice_service.mark_invoice_issued(
        invoice_id=invoice_id,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return _build_response(invoice)


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
def mark_invoice_paid(
    invoice_id: str,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Mark invoice as paid (issued -> paid). Also updates PO status."""
    invoice = invoice_service.mark_invoice_paid(
        invoice_id=invoice_id,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return _build_response(invoice)


# ─── Helper ───────────────────────────────────────────────────────────────────


def _build_response(invoice) -> InvoiceResponse:
    """Build InvoiceResponse from ORM object."""
    line_items = []
    if invoice.line_items:
        for li in invoice.line_items:
            line_items.append(InvoiceLineItemResponse(
                id=str(li.id),
                product_name=li.product_name,
                quantity=li.quantity,
                unit=li.unit,
                unit_price=li.unit_price,
                total_price=li.total_price,
            ))

    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        purchase_order_id=str(invoice.purchase_order_id) if invoice.purchase_order_id else None,
        po_number=invoice.purchase_order.po_number if invoice.purchase_order else None,
        vendor_id=str(invoice.vendor_id) if invoice.vendor_id else None,
        vendor_name=invoice.vendor.name if invoice.vendor else None,
        vendor_email=invoice.vendor.email if invoice.vendor else None,
        subtotal=invoice.subtotal,
        tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        status=invoice.status.value if hasattr(invoice.status, 'value') else str(invoice.status),
        pdf_path=invoice.pdf_path,
        notes=invoice.notes,
        paid_at=invoice.paid_at,
        generated_by=str(invoice.generated_by) if invoice.generated_by else None,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        line_items=line_items,
    )
