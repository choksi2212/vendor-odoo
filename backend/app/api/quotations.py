"""Quotation management API endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.quotation import (
    QuotationComparison,
    QuotationCreate,
    QuotationResponse,
    QuotationUpdate,
)
from app.services import quotation_service

router = APIRouter()


@router.post("", response_model=QuotationResponse, status_code=201)
def create_quotation(
    payload: QuotationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a quotation for an RFQ.
    Any authenticated user can create (vendor self-service or officer on behalf).
    """
    quotation = quotation_service.create_quotation(
        payload=payload,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return _build_response(quotation)


@router.get("/{quotation_id}", response_model=QuotationResponse)
def get_quotation(
    quotation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a quotation by ID."""
    quotation = quotation_service.get_quotation_by_id(quotation_id, db)
    return _build_response(quotation)


@router.put("/{quotation_id}", response_model=QuotationResponse)
def update_quotation(
    quotation_id: str,
    payload: QuotationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a draft quotation. Only draft quotations can be modified."""
    quotation = quotation_service.update_quotation(
        quotation_id=quotation_id,
        payload=payload,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return _build_response(quotation)


@router.post("/{quotation_id}/submit", response_model=QuotationResponse)
def submit_quotation(
    quotation_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a quotation (locks it for review). Cannot be undone."""
    quotation = quotation_service.submit_quotation(
        quotation_id=quotation_id,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    return _build_response(quotation)


@router.get("/rfq/{rfq_id}/list", response_model=list[QuotationResponse])
def list_quotations_for_rfq(
    rfq_id: str,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """List all quotations for an RFQ. Officers, Managers, and Admins only."""
    quotations = quotation_service.get_quotations_for_rfq(rfq_id, db)
    return [_build_response(q) for q in quotations]


@router.get("/rfq/{rfq_id}/compare", response_model=QuotationComparison)
def compare_quotations(
    rfq_id: str,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """
    Compare all submitted quotations for an RFQ side-by-side.
    Includes price analytics and delivery time analysis.
    """
    return quotation_service.compare_quotations(rfq_id, db)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _build_response(quotation) -> QuotationResponse:
    """Build a QuotationResponse from a Quotation ORM object."""
    return QuotationResponse(
        id=str(quotation.id),
        rfq_id=str(quotation.rfq_id),
        vendor_id=str(quotation.vendor_id),
        vendor_name=quotation.vendor.name if quotation.vendor else None,
        unit_price=quotation.unit_price,
        total_price=quotation.total_price,
        delivery_days=quotation.delivery_days,
        notes=quotation.notes,
        status=quotation.status.value if hasattr(quotation.status, 'value') else str(quotation.status),
        submitted_at=quotation.submitted_at,
        created_at=quotation.created_at,
        updated_at=quotation.updated_at,
    )
