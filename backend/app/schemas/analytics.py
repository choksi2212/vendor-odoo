"""Analytics and reporting response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Dashboard statistics overview."""
    pending_approvals: int
    active_rfqs: int
    total_vendors: int
    active_vendors: int
    total_pos_this_month: int
    total_invoices_this_month: int
    total_spend_this_month: Decimal
    total_spend_this_year: Decimal


class VendorPerformanceItem(BaseModel):
    """Single vendor's performance metrics."""
    vendor_id: str
    vendor_name: str
    total_rfqs_invited: int
    quotations_submitted: int
    submission_rate: float  # percentage
    quotations_won: int
    win_rate: float  # percentage
    total_order_value: Decimal
    average_delivery_days: Optional[float]


class VendorPerformanceResponse(BaseModel):
    """Vendor performance report."""
    vendors: list[VendorPerformanceItem]
    total_vendors: int


class MonthlyTrendItem(BaseModel):
    """Single month's trend data."""
    month: str  # YYYY-MM format
    rfqs_created: int
    quotations_received: int
    pos_issued: int
    invoices_generated: int
    total_spend: Decimal


class MonthlyTrendsResponse(BaseModel):
    """Monthly trends report."""
    months: list[MonthlyTrendItem]


class SpendingByVendorItem(BaseModel):
    """Spending breakdown per vendor."""
    vendor_id: str
    vendor_name: str
    total_amount: Decimal
    po_count: int
    percentage: float


class SpendingReportResponse(BaseModel):
    """Spending report."""
    total_spend: Decimal
    period_label: str
    breakdown: list[SpendingByVendorItem]
