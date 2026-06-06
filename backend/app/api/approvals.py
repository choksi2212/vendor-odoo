"""Approval workflow API endpoints."""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.approval import (
    ApprovalCreate,
    ApprovalDecision,
    ApprovalHistoryItem,
    ApprovalListResponse,
    ApprovalResponse,
)
from app.services import approval_service

router = APIRouter()


@router.get("", response_model=ApprovalListResponse)
def list_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter: pending, approved, rejected"),
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """List approvals with pagination and status filter."""
    approvals, total = approval_service.get_approvals(
        db=db, page=page, page_size=page_size, status_filter=status,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return ApprovalListResponse(
        items=[_build_response(a) for a in approvals],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=ApprovalResponse, status_code=201)
def create_approval(
    payload: ApprovalCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Create an approval request for a selected quotation."""
    approval = approval_service.create_approval_request(
        rfq_id=payload.rfq_id,
        quotation_id=payload.quotation_id,
        requested_by_id=str(current_user.id),
        db=db,
        request=request,
    )
    return _build_response(approval)


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: str,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Get approval details with history timeline."""
    approval = approval_service.get_approval_by_id(approval_id, db)
    return _build_response(approval)


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve(
    approval_id: str,
    payload: ApprovalDecision,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Approve a pending request. Manager and Admin only."""
    approval = approval_service.approve_request(
        approval_id=approval_id,
        approved_by_id=str(current_user.id),
        remarks=payload.remarks,
        db=db,
        request=request,
    )
    return _build_response(approval)


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject(
    approval_id: str,
    payload: ApprovalDecision,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Reject a pending request with remarks. Manager and Admin only."""
    approval = approval_service.reject_request(
        approval_id=approval_id,
        rejected_by_id=str(current_user.id),
        remarks=payload.remarks,
        db=db,
        request=request,
    )
    return _build_response(approval)


# ─── Helper ───────────────────────────────────────────────────────────────────


def _build_response(approval) -> ApprovalResponse:
    """Build ApprovalResponse from ORM object."""
    history_items = []
    if approval.history:
        for h in sorted(approval.history, key=lambda x: x.changed_at):
            history_items.append(ApprovalHistoryItem(
                id=str(h.id),
                status=h.status.value if hasattr(h.status, 'value') else str(h.status),
                remarks=h.remarks,
                changed_by=str(h.changed_by) if h.changed_by else None,
                changed_by_name=h.changer.username if hasattr(h, 'changer') and h.changer else None,
                changed_at=h.changed_at,
            ))

    return ApprovalResponse(
        id=str(approval.id),
        rfq_id=str(approval.rfq_id),
        rfq_title=approval.rfq.title if approval.rfq else None,
        quotation_id=str(approval.quotation_id),
        vendor_name=approval.quotation.vendor.name if approval.quotation and approval.quotation.vendor else None,
        total_amount=approval.quotation.total_price if approval.quotation else None,
        requested_by=str(approval.requested_by) if approval.requested_by else None,
        requested_by_name=approval.requester.username if approval.requester else None,
        approved_by=str(approval.approved_by) if approval.approved_by else None,
        approved_by_name=approval.approver.username if approval.approver else None,
        status=approval.status.value if hasattr(approval.status, 'value') else str(approval.status),
        remarks=approval.remarks,
        requested_at=approval.requested_at,
        reviewed_at=approval.reviewed_at,
        history=history_items,
    )
