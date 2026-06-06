"""
Approval workflow service.

Handles:
  - Creating approval requests (officer selects a quotation for manager approval)
  - Listing pending/all approvals
  - Approving requests (triggers downstream PO generation in future phases)
  - Rejecting requests with remarks
  - Approval history tracking (timeline)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.models.approval import Approval, ApprovalHistory, ApprovalStatus
from app.models.quotation import Quotation, QuotationStatus
from app.models.rfq import RFQ, RFQStatus
from app.models.user import User
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)


# ─── Create Approval Request ─────────────────────────────────────────────────


def create_approval_request(
    rfq_id: str,
    quotation_id: str,
    requested_by_id: str,
    db: Session,
    request: Optional[Request] = None,
) -> Approval:
    """
    Create an approval request for a selected quotation.

    Validates:
      - RFQ exists and is open or closed
      - Quotation exists, belongs to RFQ, and is submitted
      - No existing pending approval for this RFQ
    """
    # Validate RFQ
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found.")
    if rfq.status == RFQStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create approval for a draft RFQ.",
        )

    # Validate quotation
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")
    if str(quotation.rfq_id) != str(rfq_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quotation does not belong to the specified RFQ.",
        )

    # Check no existing pending approval for this RFQ (before quotation status check)
    existing = db.query(Approval).filter(
        Approval.rfq_id == rfq_id,
        Approval.status == ApprovalStatus.PENDING,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending approval already exists for this RFQ.",
        )

    if quotation.status != QuotationStatus.SUBMITTED and quotation.status != QuotationStatus.SELECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only submitted quotations can be sent for approval.",
        )

    # Create approval
    approval = Approval(
        rfq_id=rfq_id,
        quotation_id=quotation_id,
        requested_by=requested_by_id,
        status=ApprovalStatus.PENDING,
    )
    db.add(approval)
    db.flush()

    # Create initial history entry
    history = ApprovalHistory(
        approval_id=str(approval.id),
        status=ApprovalStatus.PENDING,
        remarks="Approval request submitted.",
        changed_by=requested_by_id,
    )
    db.add(history)

    # Mark quotation as selected
    quotation.status = QuotationStatus.SELECTED

    log_activity(
        db=db,
        user_id=requested_by_id,
        action="CREATE",
        entity_type="APPROVAL",
        entity_id=str(approval.id),
        details={
            "rfq_id": rfq_id,
            "quotation_id": quotation_id,
            "rfq_title": rfq.title,
        },
        request=request,
    )

    db.commit()
    db.refresh(approval)
    logger.info("Approval request created: id=%s rfq=%s", approval.id, rfq_id)
    return approval


# ─── Get Approvals ────────────────────────────────────────────────────────────


def get_approvals(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
) -> tuple[list[Approval], int]:
    """Get paginated list of approvals with optional status filter."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    query = (
        db.query(Approval)
        .options(
            joinedload(Approval.rfq),
            joinedload(Approval.quotation).joinedload(Quotation.vendor),
            joinedload(Approval.requester),
            joinedload(Approval.approver),
            joinedload(Approval.history),
        )
    )

    if status_filter:
        query = query.filter(Approval.status == status_filter)

    total = query.count()
    approvals = (
        query
        .order_by(Approval.requested_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return approvals, total


def get_approval_by_id(approval_id: str, db: Session) -> Approval:
    """Get a single approval by ID with all relationships loaded."""
    approval = (
        db.query(Approval)
        .options(
            joinedload(Approval.rfq),
            joinedload(Approval.quotation).joinedload(Quotation.vendor),
            joinedload(Approval.requester),
            joinedload(Approval.approver),
            joinedload(Approval.history).joinedload(ApprovalHistory.changer),
        )
        .filter(Approval.id == approval_id)
        .first()
    )
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found.")
    return approval


# ─── Approve ──────────────────────────────────────────────────────────────────


def approve_request(
    approval_id: str,
    approved_by_id: str,
    remarks: Optional[str],
    db: Session,
    request: Optional[Request] = None,
) -> Approval:
    """
    Approve a pending request.

    Validates:
      - Approval exists and is pending
      - Approver is not the requester (separation of duties)
    """
    approval = get_approval_by_id(approval_id, db)

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending approvals can be approved.",
        )

    # Separation of duties: requester cannot approve their own request
    if str(approval.requested_by) == str(approved_by_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot approve your own request.",
        )

    now = datetime.now(timezone.utc)
    approval.status = ApprovalStatus.APPROVED
    approval.approved_by = approved_by_id
    approval.remarks = remarks
    approval.reviewed_at = now

    # Add history entry
    history = ApprovalHistory(
        approval_id=str(approval.id),
        status=ApprovalStatus.APPROVED,
        remarks=remarks or "Approved.",
        changed_by=approved_by_id,
    )
    db.add(history)
    db.flush()

    log_activity(
        db=db,
        user_id=approved_by_id,
        action="APPROVE",
        entity_type="APPROVAL",
        entity_id=str(approval.id),
        details={
            "rfq_id": str(approval.rfq_id),
            "quotation_id": str(approval.quotation_id),
            "remarks": remarks,
        },
        request=request,
    )

    db.commit()
    db.refresh(approval)
    logger.info("Approval approved: id=%s by=%s", approval.id, approved_by_id)
    return approval


# ─── Reject ───────────────────────────────────────────────────────────────────


def reject_request(
    approval_id: str,
    rejected_by_id: str,
    remarks: Optional[str],
    db: Session,
    request: Optional[Request] = None,
) -> Approval:
    """
    Reject a pending approval request.

    Validates:
      - Approval exists and is pending
    """
    approval = get_approval_by_id(approval_id, db)

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending approvals can be rejected.",
        )

    now = datetime.now(timezone.utc)
    approval.status = ApprovalStatus.REJECTED
    approval.approved_by = rejected_by_id
    approval.remarks = remarks
    approval.reviewed_at = now

    # Revert quotation status back to submitted
    quotation = db.query(Quotation).filter(Quotation.id == approval.quotation_id).first()
    if quotation:
        quotation.status = QuotationStatus.REJECTED

    # Add history entry
    history = ApprovalHistory(
        approval_id=str(approval.id),
        status=ApprovalStatus.REJECTED,
        remarks=remarks or "Rejected.",
        changed_by=rejected_by_id,
    )
    db.add(history)
    db.flush()

    log_activity(
        db=db,
        user_id=rejected_by_id,
        action="REJECT",
        entity_type="APPROVAL",
        entity_id=str(approval.id),
        details={
            "rfq_id": str(approval.rfq_id),
            "quotation_id": str(approval.quotation_id),
            "remarks": remarks,
        },
        request=request,
    )

    db.commit()
    db.refresh(approval)
    logger.info("Approval rejected: id=%s by=%s", approval.id, rejected_by_id)
    return approval
