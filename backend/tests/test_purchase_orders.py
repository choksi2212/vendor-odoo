"""
Comprehensive Purchase Order tests for VendorBridge.

Tests cover:
  - PO generation from approved approval (success, validations)
  - Sequential PO numbering (PO-YYYY-XXXX format)
  - Tax calculation (18% GST)
  - Line item creation from RFQ data
  - PO listing with pagination and filters
  - PO status transitions (issued->paid, issued->cancelled)
  - Invalid status transitions rejected
  - Duplicate PO prevention
  - Role-based access control
"""

from datetime import date, timedelta
from decimal import Decimal


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _future_date(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


def _create_approved_approval(client, auth_headers, manager_auth_headers, quantity=100, unit_price="200.00"):
    """Create the full chain: vendor -> RFQ -> quotation -> approval (approved)."""
    # Create vendor
    v_resp = client.post("/api/vendors", headers=auth_headers, json={
        "name": "PO Test Vendor",
        "gst_number": "27AABCU9600R1ZM",
        "email": "po.vendor@test.com",
    })
    vendor = v_resp.json()

    # Create and publish RFQ
    rfq_resp = client.post("/api/rfqs", headers=auth_headers, json={
        "title": "PO Test RFQ",
        "product_name": "Industrial Widget",
        "quantity": quantity,
        "unit": "pieces",
        "deadline": _future_date(30),
    })
    rfq = rfq_resp.json()
    client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
        "vendor_ids": [vendor["id"]],
    })
    client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)

    # Create and submit quotation
    q_resp = client.post("/api/quotations", headers=auth_headers, json={
        "rfq_id": rfq["id"],
        "vendor_id": vendor["id"],
        "unit_price": unit_price,
        "delivery_days": 14,
    })
    quotation = q_resp.json()
    client.post(f"/api/quotations/{quotation['id']}/submit", headers=auth_headers)

    # Create and approve approval
    a_resp = client.post("/api/approvals", headers=auth_headers, json={
        "rfq_id": rfq["id"],
        "quotation_id": quotation["id"],
    })
    approval = a_resp.json()
    client.post(f"/api/approvals/{approval['id']}/approve", headers=manager_auth_headers, json={
        "remarks": "Approved for PO generation.",
    })

    return approval, rfq, quotation, vendor


# ─── PO Creation Tests ────────────────────────────────────────────────────────


class TestPOCreation:
    """Tests for PO generation from approved approvals."""

    def test_create_po_success(self, client, auth_headers, manager_auth_headers):
        """Generate PO from approved approval."""
        approval, rfq, quotation, vendor = _create_approved_approval(
            client, auth_headers, manager_auth_headers, quantity=100, unit_price="200.00"
        )

        response = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": approval["id"],
            "notes": "First PO for Q1 2026",
        })
        assert response.status_code == 201
        data = response.json()

        # Verify PO number format
        assert data["po_number"].startswith("PO-")
        assert len(data["po_number"].split("-")) == 3

        # Verify amounts
        assert Decimal(data["subtotal"]) == Decimal("20000.00")  # 200 * 100
        assert Decimal(data["tax_rate"]) == Decimal("18.00")  # GST
        assert Decimal(data["tax_amount"]) == Decimal("3600.00")  # 18% of 20000
        assert Decimal(data["total_amount"]) == Decimal("23600.00")  # 20000 + 3600

        # Verify status and metadata
        assert data["status"] == "issued"
        assert data["vendor_name"] == "PO Test Vendor"
        assert data["notes"] == "First PO for Q1 2026"

        # Verify line items
        assert len(data["line_items"]) == 1
        li = data["line_items"][0]
        assert li["product_name"] == "Industrial Widget"
        assert li["quantity"] == 100
        assert li["unit"] == "pieces"
        assert Decimal(li["unit_price"]) == Decimal("200.00")
        assert Decimal(li["total_price"]) == Decimal("20000.00")

    def test_create_po_sequential_numbering(self, client, auth_headers, manager_auth_headers, db_session):
        """PO numbers are sequential within the same year."""
        # Create first PO
        a1, _, _, _ = _create_approved_approval(
            client, auth_headers, manager_auth_headers, quantity=10, unit_price="50.00"
        )
        resp1 = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": a1["id"],
        })
        po1 = resp1.json()

        # Need a new vendor/RFQ/quotation/approval chain for second PO
        # Create another vendor first
        v2_resp = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Second Vendor",
            "gst_number": "27AABCU9601R1ZM",
            "email": "v2@test.com",
        })
        v2 = v2_resp.json()

        rfq2_resp = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "Second RFQ",
            "product_name": "Gadget B",
            "quantity": 20,
            "unit": "units",
            "deadline": _future_date(30),
        })
        rfq2 = rfq2_resp.json()
        client.post(f"/api/rfqs/{rfq2['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [v2["id"]],
        })
        client.post(f"/api/rfqs/{rfq2['id']}/publish", headers=auth_headers)

        q2_resp = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq2["id"],
            "vendor_id": v2["id"],
            "unit_price": "75.00",
            "delivery_days": 7,
        })
        q2 = q2_resp.json()
        client.post(f"/api/quotations/{q2['id']}/submit", headers=auth_headers)

        a2_resp = client.post("/api/approvals", headers=auth_headers, json={
            "rfq_id": rfq2["id"],
            "quotation_id": q2["id"],
        })
        a2 = a2_resp.json()
        client.post(f"/api/approvals/{a2['id']}/approve", headers=manager_auth_headers, json={})

        # Create second PO
        resp2 = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": a2["id"],
        })
        po2 = resp2.json()

        # Numbers should be sequential
        num1 = int(po1["po_number"].split("-")[-1])
        num2 = int(po2["po_number"].split("-")[-1])
        assert num2 == num1 + 1

    def test_create_po_approval_not_found(self, client, auth_headers):
        """PO creation fails for non-existent approval."""
        response = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": "00000000-0000-0000-0000-000000000000",
        })
        assert response.status_code == 404

    def test_create_po_approval_not_approved(self, client, auth_headers):
        """Cannot create PO from pending (non-approved) approval."""
        # Create vendor/RFQ/quotation/approval but don't approve
        v_resp = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Pending Vendor",
            "gst_number": "27AABCU9600R1ZM",
            "email": "pv@test.com",
        })
        vendor = v_resp.json()
        rfq_resp = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "Pending RFQ", "product_name": "Item",
            "quantity": 5, "unit": "pc", "deadline": _future_date(30),
        })
        rfq = rfq_resp.json()
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)
        q_resp = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"], "vendor_id": vendor["id"],
            "unit_price": "100.00", "delivery_days": 10,
        })
        q = q_resp.json()
        client.post(f"/api/quotations/{q['id']}/submit", headers=auth_headers)
        a_resp = client.post("/api/approvals", headers=auth_headers, json={
            "rfq_id": rfq["id"], "quotation_id": q["id"],
        })
        approval = a_resp.json()

        # Try to create PO from pending approval
        response = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": approval["id"],
        })
        assert response.status_code == 400
        assert "approved" in response.json()["detail"].lower()

    def test_create_po_duplicate_rejected(self, client, auth_headers, manager_auth_headers):
        """Cannot create a second PO for the same approval."""
        approval, _, _, _ = _create_approved_approval(
            client, auth_headers, manager_auth_headers
        )
        client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": approval["id"],
        })

        # Try again
        response = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": approval["id"],
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_create_po_vendor_forbidden(self, client, auth_headers, manager_auth_headers, vendor_auth_headers):
        """Vendor cannot create POs."""
        approval, _, _, _ = _create_approved_approval(
            client, auth_headers, manager_auth_headers
        )
        response = client.post("/api/purchase-orders", headers=vendor_auth_headers, json={
            "approval_id": approval["id"],
        })
        assert response.status_code == 403

    def test_create_po_tax_calculation(self, client, auth_headers, manager_auth_headers):
        """Tax is correctly calculated at 18% GST."""
        approval, _, _, _ = _create_approved_approval(
            client, auth_headers, manager_auth_headers, quantity=50, unit_price="1000.00"
        )
        response = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": approval["id"],
        })
        data = response.json()
        # subtotal = 1000 * 50 = 50000
        # tax = 50000 * 18% = 9000
        # total = 59000
        assert Decimal(data["subtotal"]) == Decimal("50000.00")
        assert Decimal(data["tax_amount"]) == Decimal("9000.00")
        assert Decimal(data["total_amount"]) == Decimal("59000.00")


# ─── PO Listing Tests ─────────────────────────────────────────────────────────


class TestPOListing:
    """Tests for PO listing."""

    def test_list_pos_empty(self, client, auth_headers):
        """List returns empty when no POs exist."""
        response = client.get("/api/purchase-orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_pos_with_data(self, client, auth_headers, manager_auth_headers):
        """List returns POs with correct data."""
        approval, _, _, _ = _create_approved_approval(
            client, auth_headers, manager_auth_headers
        )
        client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": approval["id"],
        })

        response = client.get("/api/purchase-orders", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "issued"
        assert len(data["items"][0]["line_items"]) == 1

    def test_list_pos_filter_by_status(self, client, auth_headers, manager_auth_headers):
        """Filter POs by status."""
        approval, _, _, _ = _create_approved_approval(
            client, auth_headers, manager_auth_headers
        )
        resp = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": approval["id"],
        })
        po_id = resp.json()["id"]

        # Mark as paid
        client.put(f"/api/purchase-orders/{po_id}/status", headers=auth_headers, json={
            "status": "paid",
        })

        # Filter issued (should be 0)
        response = client.get("/api/purchase-orders?status=issued", headers=auth_headers)
        assert response.json()["total"] == 0

        # Filter paid (should be 1)
        response = client.get("/api/purchase-orders?status=paid", headers=auth_headers)
        assert response.json()["total"] == 1

    def test_list_pos_vendor_forbidden(self, client, vendor_auth_headers):
        """Vendor cannot list POs."""
        response = client.get("/api/purchase-orders", headers=vendor_auth_headers)
        assert response.status_code == 403


# ─── PO Status Transition Tests ───────────────────────────────────────────────


class TestPOStatusTransitions:
    """Tests for PO status management."""

    def _create_po(self, client, auth_headers, manager_auth_headers):
        approval, _, _, _ = _create_approved_approval(
            client, auth_headers, manager_auth_headers
        )
        resp = client.post("/api/purchase-orders", headers=auth_headers, json={
            "approval_id": approval["id"],
        })
        return resp.json()

    def test_status_issued_to_paid(self, client, auth_headers, manager_auth_headers):
        """Transition issued -> paid."""
        po = self._create_po(client, auth_headers, manager_auth_headers)

        response = client.put(f"/api/purchase-orders/{po['id']}/status", headers=auth_headers, json={
            "status": "paid",
            "notes": "Payment received via wire transfer.",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"
        assert data["notes"] == "Payment received via wire transfer."

    def test_status_issued_to_cancelled(self, client, auth_headers, manager_auth_headers):
        """Transition issued -> cancelled."""
        po = self._create_po(client, auth_headers, manager_auth_headers)

        response = client.put(f"/api/purchase-orders/{po['id']}/status", headers=auth_headers, json={
            "status": "cancelled",
            "notes": "Vendor unable to deliver.",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_status_paid_to_anything_rejected(self, client, auth_headers, manager_auth_headers):
        """Paid is a terminal state - no transitions allowed."""
        po = self._create_po(client, auth_headers, manager_auth_headers)
        client.put(f"/api/purchase-orders/{po['id']}/status", headers=auth_headers, json={
            "status": "paid",
        })

        response = client.put(f"/api/purchase-orders/{po['id']}/status", headers=auth_headers, json={
            "status": "cancelled",
        })
        assert response.status_code == 400
        assert "terminal state" in response.json()["detail"].lower() or "cannot transition" in response.json()["detail"].lower()

    def test_status_cancelled_to_anything_rejected(self, client, auth_headers, manager_auth_headers):
        """Cancelled is a terminal state - no transitions allowed."""
        po = self._create_po(client, auth_headers, manager_auth_headers)
        client.put(f"/api/purchase-orders/{po['id']}/status", headers=auth_headers, json={
            "status": "cancelled",
        })

        response = client.put(f"/api/purchase-orders/{po['id']}/status", headers=auth_headers, json={
            "status": "paid",
        })
        assert response.status_code == 400

    def test_status_invalid_value_rejected(self, client, auth_headers, manager_auth_headers):
        """Invalid status value is rejected at schema level."""
        po = self._create_po(client, auth_headers, manager_auth_headers)

        response = client.put(f"/api/purchase-orders/{po['id']}/status", headers=auth_headers, json={
            "status": "shipped",
        })
        assert response.status_code == 422

    def test_status_po_not_found(self, client, auth_headers):
        """Updating non-existent PO returns 404."""
        response = client.put(
            "/api/purchase-orders/00000000-0000-0000-0000-000000000000/status",
            headers=auth_headers,
            json={"status": "paid"},
        )
        assert response.status_code == 404
