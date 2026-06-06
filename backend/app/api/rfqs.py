"""RFQ (Request for Quotation) management API endpoints."""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.rfq import (
    RFQCreate,
    RFQDetailResponse,
    RFQListResponse,
    RFQResponse,
    RFQUpdate,
    RFQVendorAssign,
    RFQVendorResponse,
    RFQAttachmentResponse,
)
from app.services import rfq_service

router = APIRouter()


@router.get("", response_model=RFQListResponse)
def list_rfqs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=100),
    status: Optional[str] = Query(None, description="Filter: draft, open, closed"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List RFQs with pagination and filters.
    All authenticated users can access, but results are filtered by role.
    """
    items, total = rfq_service.get_rfqs(
        db=db,
        user_role=current_user.role,
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return RFQListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=RFQResponse, status_code=201)
def create_rfq(
    payload: RFQCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Create a new RFQ. Procurement Officer and Admin only."""
    rfq = rfq_service.create_rfq(
        payload=payload,
        created_by_id=str(current_user.id),
        db=db,
        request=request,
    )
    return RFQResponse(
        id=str(rfq.id),
        title=rfq.title,
        description=rfq.description,
        product_name=rfq.product_name,
        quantity=rfq.quantity,
        unit=rfq.unit,
        deadline=rfq.deadline,
        status=rfq.status.value if hasattr(rfq.status, 'value') else str(rfq.status),
        created_by=str(rfq.created_by) if rfq.created_by else None,
        created_at=rfq.created_at,
        updated_at=rfq.updated_at,
        vendor_count=0,
        quotation_count=0,
    )


@router.get("/{rfq_id}", response_model=RFQDetailResponse)
def get_rfq(
    rfq_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get RFQ details including assigned vendors and attachments."""
    rfq = rfq_service.get_rfq_by_id(rfq_id, db)

    # Build vendor list
    vendors = []
    for va in rfq.vendor_associations:
        vendors.append(RFQVendorResponse(
            id=str(va.id),
            vendor_id=str(va.vendor_id),
            vendor_name=va.vendor.name if va.vendor else None,
            vendor_email=va.vendor.email if va.vendor else None,
            status=va.status.value if hasattr(va.status, 'value') else str(va.status),
            invited_at=va.invited_at,
        ))

    # Build attachment list
    attachments = [
        RFQAttachmentResponse(
            id=str(a.id),
            file_name=a.file_name,
            file_size=a.file_size,
            uploaded_at=a.uploaded_at,
        )
        for a in rfq.attachments
    ]

    return RFQDetailResponse(
        id=str(rfq.id),
        title=rfq.title,
        description=rfq.description,
        product_name=rfq.product_name,
        quantity=rfq.quantity,
        unit=rfq.unit,
        deadline=rfq.deadline,
        status=rfq.status.value if hasattr(rfq.status, 'value') else str(rfq.status),
        created_by=str(rfq.created_by) if rfq.created_by else None,
        created_at=rfq.created_at,
        updated_at=rfq.updated_at,
        vendor_count=len(vendors),
        quotation_count=len(rfq.quotations) if rfq.quotations else 0,
        vendors=vendors,
        attachments=attachments,
    )


@router.put("/{rfq_id}", response_model=RFQResponse)
def update_rfq(
    rfq_id: str,
    payload: RFQUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Update an RFQ. Only draft RFQs can be updated."""
    rfq = rfq_service.update_rfq(
        rfq_id=rfq_id,
        payload=payload,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return RFQResponse(
        id=str(rfq.id),
        title=rfq.title,
        description=rfq.description,
        product_name=rfq.product_name,
        quantity=rfq.quantity,
        unit=rfq.unit,
        deadline=rfq.deadline,
        status=rfq.status.value if hasattr(rfq.status, 'value') else str(rfq.status),
        created_by=str(rfq.created_by) if rfq.created_by else None,
        created_at=rfq.created_at,
        updated_at=rfq.updated_at,
    )


@router.delete("/{rfq_id}", status_code=204)
def delete_rfq(
    rfq_id: str,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Delete an RFQ. Only draft RFQs can be deleted."""
    rfq_service.delete_rfq(
        rfq_id=rfq_id,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return None


@router.post("/{rfq_id}/assign-vendors", response_model=list[RFQVendorResponse])
def assign_vendors(
    rfq_id: str,
    payload: RFQVendorAssign,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Assign vendors to an RFQ. Only draft RFQs."""
    assignments = rfq_service.assign_vendors(
        rfq_id=rfq_id,
        vendor_ids=payload.vendor_ids,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return [
        RFQVendorResponse(
            id=str(a.id),
            vendor_id=str(a.vendor_id),
            vendor_name=a.vendor.name if a.vendor else None,
            vendor_email=a.vendor.email if a.vendor else None,
            status=a.status.value if hasattr(a.status, 'value') else str(a.status),
            invited_at=a.invited_at,
        )
        for a in assignments
    ]


@router.post("/{rfq_id}/publish", response_model=RFQResponse)
def publish_rfq(
    rfq_id: str,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Publish an RFQ (draft -> open). Requires at least one vendor assigned."""
    rfq = rfq_service.publish_rfq(
        rfq_id=rfq_id,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return RFQResponse(
        id=str(rfq.id),
        title=rfq.title,
        description=rfq.description,
        product_name=rfq.product_name,
        quantity=rfq.quantity,
        unit=rfq.unit,
        deadline=rfq.deadline,
        status=rfq.status.value if hasattr(rfq.status, 'value') else str(rfq.status),
        created_by=str(rfq.created_by) if rfq.created_by else None,
        created_at=rfq.created_at,
        updated_at=rfq.updated_at,
    )


@router.post("/{rfq_id}/close", response_model=RFQResponse)
def close_rfq(
    rfq_id: str,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Close an RFQ (open -> closed). No more quotations accepted."""
    rfq = rfq_service.close_rfq(
        rfq_id=rfq_id,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return RFQResponse(
        id=str(rfq.id),
        title=rfq.title,
        description=rfq.description,
        product_name=rfq.product_name,
        quantity=rfq.quantity,
        unit=rfq.unit,
        deadline=rfq.deadline,
        status=rfq.status.value if hasattr(rfq.status, 'value') else str(rfq.status),
        created_by=str(rfq.created_by) if rfq.created_by else None,
        created_at=rfq.created_at,
        updated_at=rfq.updated_at,
    )
