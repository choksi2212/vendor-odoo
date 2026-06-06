"""
Comprehensive quotation system tests for VendorBridge.

Tests cover:
  - Quotation creation (success, validations, duplicate prevention)
  - Quotation update (draft only)
  - Quotation submission (locking behavior)
  - Quotation listing per RFQ
  - Quotation comparison with analytics
  - Role-based access control
  - Auto-calculation of total_price
  - Complete quotation workflow
"""

from datetime import date, timedelta
from decimal import Decimal


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _future_date(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


def _create_vendor(client, auth_headers, name="Test Vendor", gst_suffix="0"):
    resp = client.post("/api/vendors", headers=auth_headers, json={
        "name": name,
        "gst_number": f"27AABCU960{gst_suffix}R1ZM",
        "email": f"v{gst_suffix}@vendor.com",
    })
    assert resp.status_code == 201
    return resp.json()


def _create_open_rfq(client, auth_headers, vendor_ids, quantity=100):
    """Create an RFQ, assign vendors, and publish it."""
    rfq_resp = client.post("/api/rfqs", headers=auth_headers, json={
        "title": "Test RFQ for Quotations",
        "product_name": "Widget A",
        "quantity": quantity,
        "unit": "pieces",
        "deadline": _future_date(30),
    })
    assert rfq_resp.status_code == 201
    rfq = rfq_resp.json()

    # Assign vendors
    client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
        "vendor_ids": vendor_ids,
    })

    # Publish
    pub_resp = client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)
    assert pub_resp.status_code == 200
    return pub_resp.json()


# ─── Quotation Creation Tests ─────────────────────────────────────────────────


class TestQuotationCreation:
    """Tests for quotation creation."""

    def test_create_quotation_success(self, client, auth_headers):
        """Create a quotation for an open RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]], quantity=100)

        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "150.00",
            "delivery_days": 14,
            "notes": "Best quality guaranteed",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["rfq_id"] == rfq["id"]
        assert data["vendor_id"] == vendor["id"]
        assert Decimal(data["unit_price"]) == Decimal("150.00")
        assert Decimal(data["total_price"]) == Decimal("15000.00")  # 150 * 100
        assert data["delivery_days"] == 14
        assert data["status"] == "draft"
        assert data["notes"] == "Best quality guaranteed"

    def test_create_quotation_auto_total_calculation(self, client, auth_headers):
        """Total price is automatically calculated as unit_price * quantity."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]], quantity=50)

        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "250.50",
            "delivery_days": 7,
        })
        assert response.status_code == 201
        data = response.json()
        assert Decimal(data["total_price"]) == Decimal("12525.00")  # 250.50 * 50

    def test_create_quotation_rfq_not_found(self, client, auth_headers):
        """Cannot create quotation for non-existent RFQ."""
        vendor = _create_vendor(client, auth_headers)
        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": "00000000-0000-0000-0000-000000000000",
            "vendor_id": vendor["id"],
            "unit_price": "100.00",
            "delivery_days": 10,
        })
        assert response.status_code == 404

    def test_create_quotation_draft_rfq_rejected(self, client, auth_headers):
        """Cannot submit quotation for a draft (unpublished) RFQ."""
        vendor = _create_vendor(client, auth_headers)
        # Create RFQ but don't publish
        rfq_resp = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "Draft RFQ",
            "product_name": "Product",
            "quantity": 10,
            "unit": "pc",
            "deadline": _future_date(30),
        })
        rfq = rfq_resp.json()

        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "100.00",
            "delivery_days": 10,
        })
        assert response.status_code == 400
        assert "open" in response.json()["detail"].lower()

    def test_create_quotation_vendor_not_assigned(self, client, auth_headers):
        """Cannot submit quotation if vendor is not assigned to the RFQ."""
        vendor1 = _create_vendor(client, auth_headers, name="V1", gst_suffix="1")
        vendor2 = _create_vendor(client, auth_headers, name="V2", gst_suffix="2")
        rfq = _create_open_rfq(client, auth_headers, [vendor1["id"]])  # Only v1 assigned

        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor2["id"],  # v2 not assigned
            "unit_price": "100.00",
            "delivery_days": 10,
        })
        assert response.status_code == 403
        assert "not assigned" in response.json()["detail"].lower()

    def test_create_quotation_duplicate_rejected(self, client, auth_headers):
        """Vendor cannot submit two quotations for same RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]])

        # First quotation
        client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "100.00",
            "delivery_days": 10,
        })

        # Second quotation (same vendor, same RFQ)
        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "90.00",
            "delivery_days": 8,
        })
        assert response.status_code == 409
        assert "already submitted" in response.json()["detail"].lower()

    def test_create_quotation_zero_price_rejected(self, client, auth_headers):
        """Zero unit price is rejected."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]])

        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "0",
            "delivery_days": 10,
        })
        assert response.status_code == 422

    def test_create_quotation_negative_price_rejected(self, client, auth_headers):
        """Negative unit price is rejected."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]])

        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "-50.00",
            "delivery_days": 10,
        })
        assert response.status_code == 422

    def test_create_quotation_zero_delivery_days_rejected(self, client, auth_headers):
        """Zero delivery days is rejected."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]])

        response = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "100.00",
            "delivery_days": 0,
        })
        assert response.status_code == 422


# ─── Quotation Update Tests ───────────────────────────────────────────────────


class TestQuotationUpdate:
    """Tests for quotation update."""

    def _setup(self, client, auth_headers):
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]], quantity=100)
        resp = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "100.00",
            "delivery_days": 14,
        })
        return resp.json()

    def test_update_unit_price(self, client, auth_headers):
        """Update unit price recalculates total."""
        quotation = self._setup(client, auth_headers)

        response = client.put(
            f"/api/quotations/{quotation['id']}", headers=auth_headers, json={
                "unit_price": "120.00",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["unit_price"]) == Decimal("120.00")
        assert Decimal(data["total_price"]) == Decimal("12000.00")  # 120 * 100

    def test_update_delivery_days(self, client, auth_headers):
        """Update delivery days."""
        quotation = self._setup(client, auth_headers)

        response = client.put(
            f"/api/quotations/{quotation['id']}", headers=auth_headers, json={
                "delivery_days": 7,
            }
        )
        assert response.status_code == 200
        assert response.json()["delivery_days"] == 7

    def test_update_submitted_quotation_rejected(self, client, auth_headers):
        """Cannot update a submitted quotation."""
        quotation = self._setup(client, auth_headers)

        # Submit first
        client.post(f"/api/quotations/{quotation['id']}/submit", headers=auth_headers)

        # Try to update
        response = client.put(
            f"/api/quotations/{quotation['id']}", headers=auth_headers, json={
                "unit_price": "999.00",
            }
        )
        assert response.status_code == 400
        assert "draft" in response.json()["detail"].lower()


# ─── Quotation Submission Tests ───────────────────────────────────────────────


class TestQuotationSubmission:
    """Tests for quotation submission (locking)."""

    def _setup(self, client, auth_headers):
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]], quantity=100)
        resp = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"],
            "vendor_id": vendor["id"],
            "unit_price": "200.00",
            "delivery_days": 10,
        })
        return resp.json()

    def test_submit_quotation_success(self, client, auth_headers):
        """Submit a draft quotation."""
        quotation = self._setup(client, auth_headers)

        response = client.post(
            f"/api/quotations/{quotation['id']}/submit", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"
        assert data["submitted_at"] is not None

    def test_submit_already_submitted_rejected(self, client, auth_headers):
        """Cannot submit an already submitted quotation."""
        quotation = self._setup(client, auth_headers)
        client.post(f"/api/quotations/{quotation['id']}/submit", headers=auth_headers)

        response = client.post(
            f"/api/quotations/{quotation['id']}/submit", headers=auth_headers
        )
        assert response.status_code == 400

    def test_submit_locks_quotation(self, client, auth_headers):
        """Submitted quotation cannot be updated."""
        quotation = self._setup(client, auth_headers)
        client.post(f"/api/quotations/{quotation['id']}/submit", headers=auth_headers)

        response = client.put(
            f"/api/quotations/{quotation['id']}", headers=auth_headers, json={
                "unit_price": "1.00",
            }
        )
        assert response.status_code == 400


# ─── Quotation Listing Tests ─────────────────────────────────────────────────


class TestQuotationListing:
    """Tests for listing quotations per RFQ."""

    def test_list_quotations_for_rfq(self, client, auth_headers):
        """List all quotations for an RFQ (ordered by price)."""
        v1 = _create_vendor(client, auth_headers, name="Cheap Vendor", gst_suffix="1")
        v2 = _create_vendor(client, auth_headers, name="Expensive Vendor", gst_suffix="2")
        rfq = _create_open_rfq(client, auth_headers, [v1["id"], v2["id"]], quantity=10)

        # Submit quotations
        client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"], "vendor_id": v1["id"],
            "unit_price": "50.00", "delivery_days": 7,
        })
        client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"], "vendor_id": v2["id"],
            "unit_price": "200.00", "delivery_days": 3,
        })

        response = client.get(f"/api/quotations/rfq/{rfq['id']}/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Ordered by total_price ascending
        assert Decimal(data[0]["total_price"]) < Decimal(data[1]["total_price"])

    def test_list_quotations_empty_rfq(self, client, auth_headers):
        """List returns empty for RFQ with no quotations."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]])

        response = client.get(f"/api/quotations/rfq/{rfq['id']}/list", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_quotations_vendor_forbidden(self, client, auth_headers, vendor_auth_headers):
        """Vendor cannot list all quotations for an RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]])

        response = client.get(f"/api/quotations/rfq/{rfq['id']}/list", headers=vendor_auth_headers)
        assert response.status_code == 403


# ─── Quotation Comparison Tests ───────────────────────────────────────────────


class TestQuotationComparison:
    """Tests for quotation comparison analytics."""

    def _setup_comparison(self, client, auth_headers):
        """Create an RFQ with 3 submitted quotations."""
        v1 = _create_vendor(client, auth_headers, name="Budget Corp", gst_suffix="1")
        v2 = _create_vendor(client, auth_headers, name="Premium Inc", gst_suffix="2")
        v3 = _create_vendor(client, auth_headers, name="Mid Range Ltd", gst_suffix="3")
        rfq = _create_open_rfq(client, auth_headers, [v1["id"], v2["id"], v3["id"]], quantity=100)

        # Create and submit quotations
        for vendor_id, price, days in [(v1["id"], "80.00", 21), (v2["id"], "150.00", 7), (v3["id"], "100.00", 14)]:
            resp = client.post("/api/quotations", headers=auth_headers, json={
                "rfq_id": rfq["id"], "vendor_id": vendor_id,
                "unit_price": price, "delivery_days": days,
            })
            q_id = resp.json()["id"]
            client.post(f"/api/quotations/{q_id}/submit", headers=auth_headers)

        return rfq

    def test_compare_quotations_success(self, client, auth_headers):
        """Compare returns correct analytics."""
        rfq = self._setup_comparison(client, auth_headers)

        response = client.get(f"/api/quotations/rfq/{rfq['id']}/compare", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert data["rfq_id"] == rfq["id"]
        assert data["total_quotations"] == 3
        assert Decimal(str(data["lowest_price"])) == Decimal("8000.00")   # 80 * 100
        assert Decimal(str(data["highest_price"])) == Decimal("15000.00") # 150 * 100
        assert data["fastest_delivery"] == 7
        assert data["slowest_delivery"] == 21

    def test_compare_highlights_best(self, client, auth_headers):
        """Comparison correctly flags lowest price and fastest delivery."""
        rfq = self._setup_comparison(client, auth_headers)

        response = client.get(f"/api/quotations/rfq/{rfq['id']}/compare", headers=auth_headers)
        data = response.json()

        for q in data["quotations"]:
            if q["vendor_name"] == "Budget Corp":
                assert q["is_lowest_price"] is True
                assert q["is_fastest_delivery"] is False
            elif q["vendor_name"] == "Premium Inc":
                assert q["is_lowest_price"] is False
                assert q["is_fastest_delivery"] is True
            elif q["vendor_name"] == "Mid Range Ltd":
                assert q["is_lowest_price"] is False
                assert q["is_fastest_delivery"] is False

    def test_compare_no_submissions_rejected(self, client, auth_headers):
        """Comparison fails if no submitted quotations."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_open_rfq(client, auth_headers, [vendor["id"]])

        # Create quotation but don't submit
        client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq["id"], "vendor_id": vendor["id"],
            "unit_price": "100.00", "delivery_days": 10,
        })

        response = client.get(f"/api/quotations/rfq/{rfq['id']}/compare", headers=auth_headers)
        assert response.status_code == 400
        assert "no submitted" in response.json()["detail"].lower()

    def test_compare_vendor_forbidden(self, client, auth_headers, vendor_auth_headers):
        """Vendor cannot access comparison."""
        rfq = self._setup_comparison(client, auth_headers)
        response = client.get(f"/api/quotations/rfq/{rfq['id']}/compare", headers=vendor_auth_headers)
        assert response.status_code == 403
