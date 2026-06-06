"""
Comprehensive analytics, notifications, and activity logs tests for VendorBridge.

Tests cover:
  - Dashboard statistics (counts, spend)
  - Vendor performance metrics
  - Monthly trends
  - Spending report by vendor
  - Notification CRUD (list, mark read, mark all read)
  - Activity logs listing with filters
  - Role-based access control
"""

from datetime import date, timedelta
from decimal import Decimal


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _future_date(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


def _create_full_chain(client, auth_headers, manager_auth_headers, vendor_name="V1", gst_suffix="0", quantity=10, unit_price="100.00"):
    """Create vendor -> RFQ -> quotation -> approval -> PO -> invoice."""
    v = client.post("/api/vendors", headers=auth_headers, json={
        "name": vendor_name, "gst_number": f"27AABCU960{gst_suffix}R1ZM",
        "email": f"v{gst_suffix}@test.com",
    }).json()

    rfq = client.post("/api/rfqs", headers=auth_headers, json={
        "title": f"RFQ {gst_suffix}", "product_name": f"Product {gst_suffix}",
        "quantity": quantity, "unit": "pc", "deadline": _future_date(30),
    }).json()
    client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={"vendor_ids": [v["id"]]})
    client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)

    q = client.post("/api/quotations", headers=auth_headers, json={
        "rfq_id": rfq["id"], "vendor_id": v["id"],
        "unit_price": unit_price, "delivery_days": 14,
    }).json()
    client.post(f"/api/quotations/{q['id']}/submit", headers=auth_headers)

    a = client.post("/api/approvals", headers=auth_headers, json={
        "rfq_id": rfq["id"], "quotation_id": q["id"],
    }).json()
    client.post(f"/api/approvals/{a['id']}/approve", headers=manager_auth_headers, json={})

    po = client.post("/api/purchase-orders", headers=auth_headers, json={
        "approval_id": a["id"],
    }).json()

    inv = client.post("/api/invoices", headers=auth_headers, json={
        "purchase_order_id": po["id"],
    }).json()

    return {"vendor": v, "rfq": rfq, "quotation": q, "approval": a, "po": po, "invoice": inv}


# ─── Dashboard Tests ──────────────────────────────────────────────────────────


class TestDashboard:
    """Tests for dashboard statistics."""

    def test_dashboard_empty(self, client, auth_headers):
        """Dashboard returns zeros when no data exists."""
        response = client.get("/api/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pending_approvals"] == 0
        assert data["active_rfqs"] == 0
        assert data["total_vendors"] == 0
        assert data["active_vendors"] == 0
        assert data["total_pos_this_month"] == 0
        assert data["total_invoices_this_month"] == 0

    def test_dashboard_with_data(self, client, auth_headers, manager_auth_headers):
        """Dashboard reflects actual data."""
        _create_full_chain(client, auth_headers, manager_auth_headers, gst_suffix="0")

        response = client.get("/api/analytics/dashboard", headers=auth_headers)
        data = response.json()
        assert data["total_vendors"] == 1
        assert data["active_vendors"] == 1
        assert data["total_pos_this_month"] >= 1
        assert data["total_invoices_this_month"] >= 1
        assert Decimal(str(data["total_spend_this_month"])) > 0
        assert Decimal(str(data["total_spend_this_year"])) > 0

    def test_dashboard_pending_approvals_counted(self, client, auth_headers, manager_auth_headers):
        """Pending approvals are correctly counted."""
        # Create RFQ with quotation but leave approval pending
        v = client.post("/api/vendors", headers=auth_headers, json={
            "name": "PendV", "gst_number": "27AABCU9609R1ZM", "email": "pv@t.com",
        }).json()
        rfq = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "Pending RFQ", "product_name": "Item",
            "quantity": 5, "unit": "pc", "deadline": _future_date(30),
        }).json()
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={"vendor_ids": [v["id"]]})
        client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)
        q = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"], "vendor_id": v["id"], "unit_price": "50.00", "delivery_days": 7,
        }).json()
        client.post(f"/api/quotations/{q['id']}/submit", headers=auth_headers)
        client.post("/api/approvals", headers=auth_headers, json={
            "rfq_id": rfq["id"], "quotation_id": q["id"],
        })

        response = client.get("/api/analytics/dashboard", headers=auth_headers)
        assert response.json()["pending_approvals"] >= 1

    def test_dashboard_vendor_forbidden(self, client, vendor_auth_headers):
        """Vendor cannot access dashboard."""
        response = client.get("/api/analytics/dashboard", headers=vendor_auth_headers)
        assert response.status_code == 403


# ─── Vendor Performance Tests ─────────────────────────────────────────────────


class TestVendorPerformance:
    """Tests for vendor performance analytics."""

    def test_vendor_performance_empty(self, client, auth_headers):
        """Returns empty when no vendors."""
        response = client.get("/api/analytics/vendor-performance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_vendors"] == 0
        assert data["vendors"] == []

    def test_vendor_performance_with_data(self, client, auth_headers, manager_auth_headers):
        """Returns correct metrics for vendors."""
        _create_full_chain(client, auth_headers, manager_auth_headers, vendor_name="Perf Vendor", gst_suffix="1", quantity=50, unit_price="200.00")

        response = client.get("/api/analytics/vendor-performance", headers=auth_headers)
        data = response.json()
        assert data["total_vendors"] >= 1

        # Find our vendor
        vendor = next((v for v in data["vendors"] if v["vendor_name"] == "Perf Vendor"), None)
        assert vendor is not None
        assert vendor["total_rfqs_invited"] >= 1
        assert vendor["quotations_submitted"] >= 1
        assert vendor["submission_rate"] > 0
        assert vendor["quotations_won"] >= 1
        assert Decimal(str(vendor["total_order_value"])) > 0

    def test_vendor_performance_vendor_forbidden(self, client, vendor_auth_headers):
        """Vendor cannot access performance metrics."""
        response = client.get("/api/analytics/vendor-performance", headers=vendor_auth_headers)
        assert response.status_code == 403


# ─── Monthly Trends Tests ─────────────────────────────────────────────────────


class TestMonthlyTrends:
    """Tests for monthly trends."""

    def test_monthly_trends_returns_months(self, client, auth_headers):
        """Returns the correct number of months."""
        response = client.get("/api/analytics/monthly-trends?months=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["months"]) == 3

    def test_monthly_trends_default_6_months(self, client, auth_headers):
        """Default returns 6 months."""
        response = client.get("/api/analytics/monthly-trends", headers=auth_headers)
        data = response.json()
        assert len(data["months"]) == 6

    def test_monthly_trends_with_data(self, client, auth_headers, manager_auth_headers):
        """Trends reflect actual data."""
        _create_full_chain(client, auth_headers, manager_auth_headers, gst_suffix="2")

        response = client.get("/api/analytics/monthly-trends?months=1", headers=auth_headers)
        data = response.json()
        current_month = data["months"][0]
        assert current_month["rfqs_created"] >= 1
        assert current_month["quotations_received"] >= 1
        assert current_month["pos_issued"] >= 1
        assert current_month["invoices_generated"] >= 1

    def test_monthly_trends_vendor_forbidden(self, client, vendor_auth_headers):
        """Vendor cannot access trends."""
        response = client.get("/api/analytics/monthly-trends", headers=vendor_auth_headers)
        assert response.status_code == 403


# ─── Spending Report Tests ────────────────────────────────────────────────────


class TestSpendingReport:
    """Tests for spending breakdown."""

    def test_spending_report_empty(self, client, auth_headers):
        """Returns zero spend when no POs."""
        response = client.get("/api/analytics/spending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert Decimal(str(data["total_spend"])) == Decimal("0")
        assert data["breakdown"] == []

    def test_spending_report_with_data(self, client, auth_headers, manager_auth_headers):
        """Shows correct spending breakdown by vendor."""
        _create_full_chain(client, auth_headers, manager_auth_headers, vendor_name="Spend V1", gst_suffix="3", quantity=10, unit_price="500.00")

        response = client.get("/api/analytics/spending", headers=auth_headers)
        data = response.json()
        assert Decimal(str(data["total_spend"])) > 0
        assert len(data["breakdown"]) >= 1

        vendor_entry = data["breakdown"][0]
        assert vendor_entry["vendor_name"] == "Spend V1"
        assert vendor_entry["po_count"] == 1
        assert vendor_entry["percentage"] > 0


# ─── Notification Tests ───────────────────────────────────────────────────────


class TestNotifications:
    """Tests for notification endpoints."""

    def _create_notification(self, db_session, user_id):
        """Helper to create a notification directly in DB."""
        from app.models.notification import Notification, NotificationType
        n = Notification(
            user_id=user_id,
            type=NotificationType.INFO,
            title="Test Notification",
            message="This is a test notification.",
            entity_type="RFQ",
        )
        db_session.add(n)
        db_session.commit()
        db_session.refresh(n)
        return n

    def test_list_notifications_empty(self, client, auth_headers):
        """Returns empty when no notifications."""
        response = client.get("/api/notifications/my", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_notifications_with_data(self, client, auth_headers, test_user, db_session):
        """Returns user's notifications."""
        self._create_notification(db_session, str(test_user.id))
        self._create_notification(db_session, str(test_user.id))

        response = client.get("/api/notifications/my", headers=auth_headers)
        data = response.json()
        assert data["total"] == 2

    def test_list_notifications_unread_filter(self, client, auth_headers, test_user, db_session):
        """Filter unread notifications."""
        n = self._create_notification(db_session, str(test_user.id))
        self._create_notification(db_session, str(test_user.id))

        # Mark one as read
        client.put(f"/api/notifications/{n.id}/read", headers=auth_headers)

        response = client.get("/api/notifications/my?unread_only=true", headers=auth_headers)
        assert response.json()["total"] == 1

    def test_mark_notification_read(self, client, auth_headers, test_user, db_session):
        """Mark single notification as read."""
        n = self._create_notification(db_session, str(test_user.id))

        response = client.put(f"/api/notifications/{n.id}/read", headers=auth_headers)
        assert response.status_code == 200

        # Verify it's read
        list_resp = client.get("/api/notifications/my?unread_only=true", headers=auth_headers)
        assert list_resp.json()["total"] == 0

    def test_mark_all_read(self, client, auth_headers, test_user, db_session):
        """Mark all notifications as read."""
        self._create_notification(db_session, str(test_user.id))
        self._create_notification(db_session, str(test_user.id))
        self._create_notification(db_session, str(test_user.id))

        response = client.put("/api/notifications/mark-all-read", headers=auth_headers)
        assert response.status_code == 200

        list_resp = client.get("/api/notifications/my?unread_only=true", headers=auth_headers)
        assert list_resp.json()["total"] == 0

    def test_mark_notification_not_found(self, client, auth_headers):
        """Mark non-existent notification returns 404."""
        response = client.put(
            "/api/notifications/00000000-0000-0000-0000-000000000000/read",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ─── Activity Logs Tests ──────────────────────────────────────────────────────


class TestActivityLogs:
    """Tests for activity logs endpoint."""

    def test_list_activity_logs_admin(self, client, admin_auth_headers, auth_headers):
        """Admin can view activity logs."""
        # Create some activity by creating a vendor
        client.post("/api/vendors", headers=auth_headers, json={
            "name": "Log Test Vendor", "gst_number": "27AABCU9600R1ZM", "email": "lt@t.com",
        })

        response = client.get("/api/activity-logs", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["items"][0]["action"] == "CREATE"
        assert data["items"][0]["entity_type"] == "VENDOR"

    def test_list_activity_logs_filter_by_entity(self, client, admin_auth_headers, auth_headers):
        """Filter logs by entity type."""
        client.post("/api/vendors", headers=auth_headers, json={
            "name": "Filter Vendor", "gst_number": "27AABCU9601R1ZM", "email": "fv@t.com",
        })

        response = client.get("/api/activity-logs?entity_type=VENDOR", headers=admin_auth_headers)
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["entity_type"] == "VENDOR"

    def test_list_activity_logs_officer_forbidden(self, client, auth_headers):
        """Non-admin cannot view activity logs."""
        response = client.get("/api/activity-logs", headers=auth_headers)
        assert response.status_code == 403

    def test_list_activity_logs_vendor_forbidden(self, client, vendor_auth_headers):
        """Vendor cannot view activity logs."""
        response = client.get("/api/activity-logs", headers=vendor_auth_headers)
        assert response.status_code == 403
