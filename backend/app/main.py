"""VendorBridge API - Enterprise-Grade Procurement & Vendor Management System."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.security import limiter
from app.api import auth, users, vendors, rfqs, quotations, approvals, purchase_orders, invoices, analytics, notifications, activity_logs, websocket as ws_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting VendorBridge API...")
    logger.info("Environment: %s", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down VendorBridge API...")


# Create FastAPI application
app = FastAPI(
    title="VendorBridge API",
    description="Enterprise-Grade Procurement & Vendor Management ERP System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please contact support."},
    )


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "VendorBridge API",
        "version": "1.0.0",
    }


# Register routers - Phase 3: Auth & Users
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])

# Register routers - Phase 4: Vendors
app.include_router(vendors.router, prefix="/api/vendors", tags=["Vendors"])

# Register routers - Phase 5: RFQs
app.include_router(rfqs.router, prefix="/api/rfqs", tags=["RFQs"])

# Register routers - Phase 6: Quotations
app.include_router(quotations.router, prefix="/api/quotations", tags=["Quotations"])

# Register routers - Phase 7: Approvals
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])

# Register routers - Phase 8: Purchase Orders
app.include_router(purchase_orders.router, prefix="/api/purchase-orders", tags=["Purchase Orders"])

# Register routers - Phase 9: Invoices
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])

# Register routers - Phase 10: Analytics, Notifications, Activity Logs
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(activity_logs.router, prefix="/api/activity-logs", tags=["Activity Logs"])

# Register routers - Phase 11: WebSocket
app.include_router(ws_api.router, prefix="/api/ws", tags=["WebSocket"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to VendorBridge API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
