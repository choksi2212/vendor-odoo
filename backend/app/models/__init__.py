"""
Import all models to ensure SQLAlchemy relationship resolution works correctly.
All models must be imported before any relationship() can be resolved.
"""

from app.models.user import User, UserSession, OneTimeToken, OTPCode, UserRole, TokenPurpose
from app.models.vendor import Vendor, VendorCategory, VendorStatus
from app.models.rfq import RFQ, RFQVendor, RFQAttachment, RFQStatus, RFQVendorStatus
from app.models.quotation import Quotation, QuotationStatus
from app.models.approval import Approval, ApprovalHistory, ApprovalStatus
from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus
from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.activity_log import ActivityLog
from app.models.notification import Notification, NotificationType

__all__ = [
    "User", "UserSession", "OneTimeToken", "OTPCode", "UserRole", "TokenPurpose",
    "Vendor", "VendorCategory", "VendorStatus",
    "RFQ", "RFQVendor", "RFQAttachment", "RFQStatus", "RFQVendorStatus",
    "Quotation", "QuotationStatus",
    "Approval", "ApprovalHistory", "ApprovalStatus",
    "PurchaseOrder", "POLineItem", "POStatus",
    "Invoice", "InvoiceLineItem", "InvoiceStatus",
    "ActivityLog",
    "Notification", "NotificationType",
]

