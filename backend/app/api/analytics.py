"""Analytics and reporting API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.analytics import (
    DashboardStats,
    MonthlyTrendsResponse,
    SpendingReportResponse,
    VendorPerformanceResponse,
)
from app.services import analytics_service

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics overview."""
    return analytics_service.get_dashboard_stats(db)


@router.get("/vendor-performance", response_model=VendorPerformanceResponse)
def get_vendor_performance(
    limit: int = Query(20, ge=1, le=100, description="Max vendors to return"),
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Get vendor performance metrics."""
    return analytics_service.get_vendor_performance(db, limit=limit)


@router.get("/monthly-trends", response_model=MonthlyTrendsResponse)
def get_monthly_trends(
    months: int = Query(6, ge=1, le=12, description="Number of months to include"),
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Get monthly trends for the last N months."""
    return analytics_service.get_monthly_trends(db, months=months)


@router.get("/spending", response_model=SpendingReportResponse)
def get_spending_report(
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER, UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """Get spending breakdown by vendor."""
    return analytics_service.get_spending_report(db)
