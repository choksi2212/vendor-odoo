"""
Analytics and reporting service.

Provides:
  - Dashboard statistics (counts, spend totals)
  - Vendor performance metrics
  - Monthly trends
  - Spending reports by vendor
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, extract, and_
from sqlalchemy.orm import Session

from app.models.approval import Approval, ApprovalStatus
from app.models.invoice import Invoice
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.quotation import Quotation, QuotationStatus
from app.models.rfq import RFQ, RFQStatus, RFQVendor
from app.models.vendor import Vendor, VendorStatus

logger = logging.getLogger(__name__)


def get_dashboard_stats(db: Session) -> dict:
    """
    Get dashboard overview statistics.
    
    Returns counts and monetary totals for the current period.
    """
    now = datetime.now(timezone.utc)
    current_month = now.month
    current_year = now.year

    # Pending approvals
    pending_approvals = db.query(func.count(Approval.id)).filter(
        Approval.status == ApprovalStatus.PENDING
    ).scalar() or 0

    # Active RFQs (open status)
    active_rfqs = db.query(func.count(RFQ.id)).filter(
        RFQ.status == RFQStatus.OPEN
    ).scalar() or 0

    # Vendors
    total_vendors = db.query(func.count(Vendor.id)).scalar() or 0
    active_vendors = db.query(func.count(Vendor.id)).filter(
        Vendor.status == VendorStatus.ACTIVE
    ).scalar() or 0

    # POs this month
    total_pos_this_month = db.query(func.count(PurchaseOrder.id)).filter(
        extract("year", PurchaseOrder.created_at) == current_year,
        extract("month", PurchaseOrder.created_at) == current_month,
    ).scalar() or 0

    # Invoices this month
    total_invoices_this_month = db.query(func.count(Invoice.id)).filter(
        extract("year", Invoice.created_at) == current_year,
        extract("month", Invoice.created_at) == current_month,
    ).scalar() or 0

    # Spend this month (from issued/paid POs)
    spend_this_month = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        extract("year", PurchaseOrder.created_at) == current_year,
        extract("month", PurchaseOrder.created_at) == current_month,
        PurchaseOrder.status.in_([POStatus.ISSUED, POStatus.PAID]),
    ).scalar() or Decimal("0.00")

    # Spend this year
    spend_this_year = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        extract("year", PurchaseOrder.created_at) == current_year,
        PurchaseOrder.status.in_([POStatus.ISSUED, POStatus.PAID]),
    ).scalar() or Decimal("0.00")

    return {
        "pending_approvals": pending_approvals,
        "active_rfqs": active_rfqs,
        "total_vendors": total_vendors,
        "active_vendors": active_vendors,
        "total_pos_this_month": total_pos_this_month,
        "total_invoices_this_month": total_invoices_this_month,
        "total_spend_this_month": spend_this_month,
        "total_spend_this_year": spend_this_year,
    }


def get_vendor_performance(db: Session, limit: int = 20) -> dict:
    """
    Get vendor performance metrics.
    
    For each vendor calculates:
      - Total RFQs invited to
      - Quotations submitted
      - Submission rate (quotations / invitations)
      - Quotations won (selected/approved)
      - Win rate
      - Total order value
      - Average delivery days quoted
    """
    vendors = db.query(Vendor).filter(Vendor.status == VendorStatus.ACTIVE).limit(limit).all()

    results = []
    for vendor in vendors:
        # RFQs invited
        rfqs_invited = db.query(func.count(RFQVendor.id)).filter(
            RFQVendor.vendor_id == vendor.id
        ).scalar() or 0

        # Quotations submitted
        quotations_submitted = db.query(func.count(Quotation.id)).filter(
            Quotation.vendor_id == vendor.id,
            Quotation.status.in_([QuotationStatus.SUBMITTED, QuotationStatus.SELECTED]),
        ).scalar() or 0

        # Quotations won (selected status)
        quotations_won = db.query(func.count(Quotation.id)).filter(
            Quotation.vendor_id == vendor.id,
            Quotation.status == QuotationStatus.SELECTED,
        ).scalar() or 0

        # Total order value
        total_order_value = db.query(func.sum(PurchaseOrder.total_amount)).filter(
            PurchaseOrder.vendor_id == vendor.id,
            PurchaseOrder.status.in_([POStatus.ISSUED, POStatus.PAID]),
        ).scalar() or Decimal("0.00")

        # Average delivery days
        avg_delivery = db.query(func.avg(Quotation.delivery_days)).filter(
            Quotation.vendor_id == vendor.id,
            Quotation.status.in_([QuotationStatus.SUBMITTED, QuotationStatus.SELECTED]),
        ).scalar()

        submission_rate = (quotations_submitted / rfqs_invited * 100) if rfqs_invited > 0 else 0.0
        win_rate = (quotations_won / quotations_submitted * 100) if quotations_submitted > 0 else 0.0

        results.append({
            "vendor_id": str(vendor.id),
            "vendor_name": vendor.name,
            "total_rfqs_invited": rfqs_invited,
            "quotations_submitted": quotations_submitted,
            "submission_rate": round(submission_rate, 1),
            "quotations_won": quotations_won,
            "win_rate": round(win_rate, 1),
            "total_order_value": total_order_value,
            "average_delivery_days": round(avg_delivery, 1) if avg_delivery else None,
        })

    return {
        "vendors": results,
        "total_vendors": len(results),
    }


def get_monthly_trends(db: Session, months: int = 6) -> dict:
    """
    Get monthly trends for the last N months.
    
    For each month returns:
      - RFQs created
      - Quotations received
      - POs issued
      - Invoices generated
      - Total spend
    """
    now = datetime.now(timezone.utc)
    results = []

    for i in range(months - 1, -1, -1):
        # Calculate target month
        target_month = now.month - i
        target_year = now.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        month_label = f"{target_year}-{target_month:02d}"

        rfqs_created = db.query(func.count(RFQ.id)).filter(
            extract("year", RFQ.created_at) == target_year,
            extract("month", RFQ.created_at) == target_month,
        ).scalar() or 0

        quotations_received = db.query(func.count(Quotation.id)).filter(
            extract("year", Quotation.created_at) == target_year,
            extract("month", Quotation.created_at) == target_month,
        ).scalar() or 0

        pos_issued = db.query(func.count(PurchaseOrder.id)).filter(
            extract("year", PurchaseOrder.created_at) == target_year,
            extract("month", PurchaseOrder.created_at) == target_month,
        ).scalar() or 0

        invoices_generated = db.query(func.count(Invoice.id)).filter(
            extract("year", Invoice.created_at) == target_year,
            extract("month", Invoice.created_at) == target_month,
        ).scalar() or 0

        total_spend = db.query(func.sum(PurchaseOrder.total_amount)).filter(
            extract("year", PurchaseOrder.created_at) == target_year,
            extract("month", PurchaseOrder.created_at) == target_month,
            PurchaseOrder.status.in_([POStatus.ISSUED, POStatus.PAID]),
        ).scalar() or Decimal("0.00")

        results.append({
            "month": month_label,
            "rfqs_created": rfqs_created,
            "quotations_received": quotations_received,
            "pos_issued": pos_issued,
            "invoices_generated": invoices_generated,
            "total_spend": total_spend,
        })

    return {"months": results}


def get_spending_report(db: Session) -> dict:
    """
    Get spending breakdown by vendor.
    
    Returns total spend and per-vendor breakdown with percentages.
    """
    # Total spend from issued/paid POs
    total_spend = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.status.in_([POStatus.ISSUED, POStatus.PAID]),
    ).scalar() or Decimal("0.00")

    # Breakdown by vendor
    vendor_spending = (
        db.query(
            Vendor.id,
            Vendor.name,
            func.sum(PurchaseOrder.total_amount).label("total"),
            func.count(PurchaseOrder.id).label("po_count"),
        )
        .join(PurchaseOrder, PurchaseOrder.vendor_id == Vendor.id)
        .filter(PurchaseOrder.status.in_([POStatus.ISSUED, POStatus.PAID]))
        .group_by(Vendor.id, Vendor.name)
        .order_by(func.sum(PurchaseOrder.total_amount).desc())
        .all()
    )

    breakdown = []
    for row in vendor_spending:
        percentage = (float(row.total) / float(total_spend) * 100) if total_spend > 0 else 0.0
        breakdown.append({
            "vendor_id": str(row.id),
            "vendor_name": row.name,
            "total_amount": row.total,
            "po_count": row.po_count,
            "percentage": round(percentage, 1),
        })

    return {
        "total_spend": total_spend,
        "period_label": "All Time",
        "breakdown": breakdown,
    }
