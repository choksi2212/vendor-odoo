"""Purchase Order management API endpoints."""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.purchase_order import (
    POCreate,
    POLineItemResponse,
    POListResponse,
    POResponse,
    POStatusUpdate,
)
from app.services import purchase_order_service

router = APIRouter()


@router.get("", response_model=POListResponse)
def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter: issued, paid, cancelled"),
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """List Purchase Orders with pagination and status filter."""
    pos, total = purchase_order_service.get_purchase_orders(
        db=db, page=page, page_size=page_size, status_filter=status,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return POListResponse(
        items=[_build_response(po) for po in pos],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=POResponse, status_code=201)
def create_purchase_order(
    payload: POCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Create a Purchase Order from an approved approval."""
    po = purchase_order_service.create_po_from_approval(
        approval_id=payload.approval_id,
        created_by_id=str(current_user.id),
        notes=payload.notes,
        db=db,
        request=request,
    )
    return _build_response(po)


@router.get("/{po_id}", response_model=POResponse)
def get_purchase_order(
    po_id: str,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Get Purchase Order details."""
    po = purchase_order_service.get_po_by_id(po_id, db)
    return _build_response(po)


@router.put("/{po_id}/status", response_model=POResponse)
def update_po_status(
    po_id: str,
    payload: POStatusUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Update PO status. Valid transitions: issued->paid, issued->cancelled."""
    po = purchase_order_service.update_po_status(
        po_id=po_id,
        new_status=payload.status,
        user_id=str(current_user.id),
        notes=payload.notes,
        db=db,
        request=request,
    )
    return _build_response(po)


# ─── Helper ───────────────────────────────────────────────────────────────────


def _build_response(po: object) -> POResponse:
    """Build POResponse from ORM object."""
    line_items = []
    if po.line_items:
        for li in po.line_items:
            line_items.append(POLineItemResponse(
                id=str(li.id),
                product_name=li.product_name,
                quantity=li.quantity,
                unit=li.unit,
                unit_price=li.unit_price,
                total_price=li.total_price,
            ))

    return POResponse(
        id=str(po.id),
        po_number=po.po_number,
        approval_id=str(po.approval_id) if po.approval_id else None,
        quotation_id=str(po.quotation_id) if po.quotation_id else None,
        vendor_id=str(po.vendor_id) if po.vendor_id else None,
        vendor_name=po.vendor.name if po.vendor else None,
        subtotal=po.subtotal,
        tax_rate=po.tax_rate,
        tax_amount=po.tax_amount,
        total_amount=po.total_amount,
        status=po.status.value if hasattr(po.status, 'value') else str(po.status),
        notes=po.notes,
        created_by=str(po.created_by) if po.created_by else None,
        created_at=po.created_at,
        updated_at=po.updated_at,
        line_items=line_items,
    )
