"""
Comprehensive RFQ management tests for VendorBridge.

Tests cover:
  - RFQ creation (success, validation, role checks)
  - RFQ listing (pagination, search, status filter)
  - RFQ detail view
  - RFQ update (draft only enforcement)
  - RFQ deletion (draft only enforcement)
  - Vendor assignment to RFQs
  - RFQ publishing (draft -> open with vendor requirement)
  - RFQ closing (open -> closed)
  - Complete RFQ lifecycle workflow
"""

from datetime import date, timedelta


# ─── Helper ───────────────────────────────────────────────────────────────────

def _future_date(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


def _create_rfq(client, auth_headers, **overrides):
    """Helper to create an RFQ for testing."""
    data = {
        "title": "Office Laptops Procurement",
        "description": "Need 50 high-spec laptops for dev team",
        "product_name": "Laptop Dell XPS 15",
        "quantity": 50,
        "unit": "pieces",
        "deadline": _future_date(30),
    }
    data.update(overrides)
    resp = client.post("/api/rfqs", headers=auth_headers, json=data)
    assert resp.status_code == 201, f"Create RFQ failed: {resp.json()}"
    return resp.json()


def _create_vendor(client, auth_headers, name="Test Vendor", gst_suffix="0"):
    """Helper to create a vendor."""
    resp = client.post("/api/vendors", headers=auth_headers, json={
        "name": name,
        "gst_number": f"27AABCU960{gst_suffix}R1ZM",
        "email": f"v{gst_suffix}@vendor.com",
    })
    assert resp.status_code == 201
    return resp.json()


# ─── RFQ Creation Tests ──────────────────────────────────────────────────────


class TestRFQCreation:
    """Tests for RFQ creation endpoint."""

    def test_create_rfq_success(self, client, auth_headers):
        """Procurement officer can create an RFQ."""
        response = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "Office Supplies Q1 2026",
            "description": "Quarterly procurement of office supplies",
            "product_name": "A4 Paper Reams",
            "quantity": 500,
            "unit": "reams",
            "deadline": _future_date(45),
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Office Supplies Q1 2026"
        assert data["product_name"] == "A4 Paper Reams"
        assert data["quantity"] == 500
        assert data["unit"] == "reams"
        assert data["status"] == "draft"
        assert "id" in data

    def test_create_rfq_admin(self, client, admin_auth_headers):
        """Admin can create an RFQ."""
        response = client.post("/api/rfqs", headers=admin_auth_headers, json={
            "title": "Server Procurement",
            "product_name": "Dell PowerEdge R750",
            "quantity": 10,
            "unit": "units",
            "deadline": _future_date(60),
        })
        assert response.status_code == 201

    def test_create_rfq_vendor_forbidden(self, client, vendor_auth_headers):
        """Vendor cannot create RFQs."""
        response = client.post("/api/rfqs", headers=vendor_auth_headers, json={
            "title": "Test",
            "product_name": "Test",
            "quantity": 1,
            "unit": "pc",
            "deadline": _future_date(30),
        })
        assert response.status_code == 403

    def test_create_rfq_manager_forbidden(self, client, manager_auth_headers):
        """Manager cannot create RFQs."""
        response = client.post("/api/rfqs", headers=manager_auth_headers, json={
            "title": "Test",
            "product_name": "Test",
            "quantity": 1,
            "unit": "pc",
            "deadline": _future_date(30),
        })
        assert response.status_code == 403

    def test_create_rfq_past_deadline_rejected(self, client, auth_headers):
        """RFQ with past deadline is rejected."""
        response = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "Late RFQ",
            "product_name": "Product",
            "quantity": 10,
            "unit": "pc",
            "deadline": "2020-01-01",
        })
        assert response.status_code == 422

    def test_create_rfq_zero_quantity_rejected(self, client, auth_headers):
        """RFQ with zero quantity is rejected."""
        response = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "Bad RFQ",
            "product_name": "Product",
            "quantity": 0,
            "unit": "pc",
            "deadline": _future_date(30),
        })
        assert response.status_code == 422

    def test_create_rfq_negative_quantity_rejected(self, client, auth_headers):
        """RFQ with negative quantity is rejected."""
        response = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "Bad RFQ",
            "product_name": "Product",
            "quantity": -5,
            "unit": "pc",
            "deadline": _future_date(30),
        })
        assert response.status_code == 422

    def test_create_rfq_empty_title_rejected(self, client, auth_headers):
        """RFQ with empty title is rejected."""
        response = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "",
            "product_name": "Product",
            "quantity": 10,
            "unit": "pc",
            "deadline": _future_date(30),
        })
        assert response.status_code == 422


# ─── RFQ Listing Tests ────────────────────────────────────────────────────────


class TestRFQListing:
    """Tests for RFQ listing with pagination and filters."""

    def test_list_rfqs_empty(self, client, auth_headers):
        """List returns empty when no RFQs exist."""
        response = client.get("/api/rfqs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_rfqs_pagination(self, client, auth_headers):
        """Pagination works correctly."""
        for i in range(5):
            _create_rfq(client, auth_headers, title=f"RFQ {i}", product_name=f"Product {i}")

        response = client.get("/api/rfqs?page=1&page_size=2", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3

    def test_list_rfqs_search(self, client, auth_headers):
        """Search by title and product name."""
        _create_rfq(client, auth_headers, title="Laptop Procurement", product_name="Dell XPS")
        _create_rfq(client, auth_headers, title="Chair Procurement", product_name="Herman Miller")

        response = client.get("/api/rfqs?search=Laptop", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1
        assert "Laptop" in data["items"][0]["title"]

    def test_list_rfqs_filter_by_status(self, client, auth_headers):
        """Filter by status."""
        _create_rfq(client, auth_headers, title="Draft RFQ")

        response = client.get("/api/rfqs?status=draft", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "draft"

        response = client.get("/api/rfqs?status=open", headers=auth_headers)
        data = response.json()
        assert data["total"] == 0


# ─── RFQ Detail Tests ─────────────────────────────────────────────────────────


class TestRFQDetail:
    """Tests for getting RFQ details."""

    def test_get_rfq_success(self, client, auth_headers):
        """Get RFQ by ID with full details."""
        rfq = _create_rfq(client, auth_headers)
        response = client.get(f"/api/rfqs/{rfq['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rfq["id"]
        assert data["title"] == rfq["title"]
        assert "vendors" in data
        assert "attachments" in data

    def test_get_rfq_not_found(self, client, auth_headers):
        """Get non-existent RFQ returns 404."""
        response = client.get(
            "/api/rfqs/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_rfq_with_vendors(self, client, auth_headers):
        """Get RFQ shows assigned vendors."""
        vendor = _create_vendor(client, auth_headers, name="Assigned Vendor")
        rfq = _create_rfq(client, auth_headers)

        # Assign vendor
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })

        response = client.get(f"/api/rfqs/{rfq['id']}", headers=auth_headers)
        data = response.json()
        assert len(data["vendors"]) == 1
        assert data["vendors"][0]["vendor_name"] == "Assigned Vendor"
        assert data["vendor_count"] == 1


# ─── RFQ Update Tests ─────────────────────────────────────────────────────────


class TestRFQUpdate:
    """Tests for RFQ update endpoint."""

    def test_update_rfq_title(self, client, auth_headers):
        """Update RFQ title."""
        rfq = _create_rfq(client, auth_headers)
        response = client.put(f"/api/rfqs/{rfq['id']}", headers=auth_headers, json={
            "title": "Updated Title",
        })
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_update_rfq_quantity(self, client, auth_headers):
        """Update RFQ quantity."""
        rfq = _create_rfq(client, auth_headers)
        response = client.put(f"/api/rfqs/{rfq['id']}", headers=auth_headers, json={
            "quantity": 100,
        })
        assert response.status_code == 200
        assert response.json()["quantity"] == 100

    def test_update_open_rfq_rejected(self, client, auth_headers):
        """Cannot update an open RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_rfq(client, auth_headers)
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)

        response = client.put(f"/api/rfqs/{rfq['id']}", headers=auth_headers, json={
            "title": "Changed",
        })
        assert response.status_code == 400
        assert "draft" in response.json()["detail"].lower()


# ─── RFQ Delete Tests ─────────────────────────────────────────────────────────


class TestRFQDelete:
    """Tests for RFQ deletion."""

    def test_delete_draft_rfq(self, client, auth_headers):
        """Can delete a draft RFQ."""
        rfq = _create_rfq(client, auth_headers)
        response = client.delete(f"/api/rfqs/{rfq['id']}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/api/rfqs/{rfq['id']}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_open_rfq_rejected(self, client, auth_headers):
        """Cannot delete an open RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_rfq(client, auth_headers)
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)

        response = client.delete(f"/api/rfqs/{rfq['id']}", headers=auth_headers)
        assert response.status_code == 400

    def test_delete_rfq_vendor_forbidden(self, client, auth_headers, vendor_auth_headers):
        """Vendor cannot delete RFQs."""
        rfq = _create_rfq(client, auth_headers)
        response = client.delete(f"/api/rfqs/{rfq['id']}", headers=vendor_auth_headers)
        assert response.status_code == 403


# ─── Vendor Assignment Tests ──────────────────────────────────────────────────


class TestVendorAssignment:
    """Tests for assigning vendors to RFQs."""

    def test_assign_vendor_success(self, client, auth_headers):
        """Assign a vendor to an RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_rfq(client, auth_headers)

        response = client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["vendor_id"] == vendor["id"]
        assert data[0]["status"] == "invited"

    def test_assign_multiple_vendors(self, client, auth_headers):
        """Assign multiple vendors at once."""
        v1 = _create_vendor(client, auth_headers, name="Vendor 1", gst_suffix="1")
        v2 = _create_vendor(client, auth_headers, name="Vendor 2", gst_suffix="2")
        v3 = _create_vendor(client, auth_headers, name="Vendor 3", gst_suffix="3")
        rfq = _create_rfq(client, auth_headers)

        response = client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [v1["id"], v2["id"], v3["id"]],
        })
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_assign_duplicate_vendor_idempotent(self, client, auth_headers):
        """Assigning same vendor twice doesn't create duplicate."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_rfq(client, auth_headers)

        # First assignment
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        # Second assignment (same vendor)
        response = client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        assert response.status_code == 200

        # Check RFQ detail - should only have 1 vendor
        detail = client.get(f"/api/rfqs/{rfq['id']}", headers=auth_headers)
        assert len(detail.json()["vendors"]) == 1

    def test_assign_nonexistent_vendor(self, client, auth_headers):
        """Assigning non-existent vendor fails."""
        rfq = _create_rfq(client, auth_headers)
        response = client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": ["00000000-0000-0000-0000-000000000000"],
        })
        assert response.status_code == 404

    def test_assign_inactive_vendor_rejected(self, client, auth_headers):
        """Cannot assign inactive vendor."""
        vendor = _create_vendor(client, auth_headers)
        # Deactivate vendor
        client.delete(f"/api/vendors/{vendor['id']}", headers=auth_headers)

        rfq = _create_rfq(client, auth_headers)
        response = client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()

    def test_assign_to_open_rfq_rejected(self, client, auth_headers):
        """Cannot assign vendors to published (open) RFQ."""
        vendor1 = _create_vendor(client, auth_headers, name="V1", gst_suffix="1")
        vendor2 = _create_vendor(client, auth_headers, name="V2", gst_suffix="2")
        rfq = _create_rfq(client, auth_headers)

        # Assign first vendor and publish
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor1["id"]],
        })
        client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)

        # Try to assign another vendor
        response = client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor2["id"]],
        })
        assert response.status_code == 400


# ─── RFQ Publishing Tests ─────────────────────────────────────────────────────


class TestRFQPublish:
    """Tests for RFQ publishing (draft -> open)."""

    def test_publish_rfq_success(self, client, auth_headers):
        """Publish RFQ with vendors assigned."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_rfq(client, auth_headers)
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })

        response = client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "open"

    def test_publish_without_vendors_rejected(self, client, auth_headers):
        """Cannot publish RFQ without vendors."""
        rfq = _create_rfq(client, auth_headers)
        response = client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)
        assert response.status_code == 400
        assert "vendor" in response.json()["detail"].lower()

    def test_publish_already_open_rejected(self, client, auth_headers):
        """Cannot publish an already open RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_rfq(client, auth_headers)
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)

        response = client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)
        assert response.status_code == 400


# ─── RFQ Closing Tests ────────────────────────────────────────────────────────


class TestRFQClose:
    """Tests for RFQ closing (open -> closed)."""

    def test_close_rfq_success(self, client, auth_headers):
        """Close an open RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_rfq(client, auth_headers)
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)

        response = client.post(f"/api/rfqs/{rfq['id']}/close", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "closed"

    def test_close_draft_rfq_rejected(self, client, auth_headers):
        """Cannot close a draft RFQ."""
        rfq = _create_rfq(client, auth_headers)
        response = client.post(f"/api/rfqs/{rfq['id']}/close", headers=auth_headers)
        assert response.status_code == 400

    def test_close_already_closed_rejected(self, client, auth_headers):
        """Cannot close an already closed RFQ."""
        vendor = _create_vendor(client, auth_headers)
        rfq = _create_rfq(client, auth_headers)
        client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)
        client.post(f"/api/rfqs/{rfq['id']}/close", headers=auth_headers)

        response = client.post(f"/api/rfqs/{rfq['id']}/close", headers=auth_headers)
        assert response.status_code == 400


# ─── Full Lifecycle Test ──────────────────────────────────────────────────────


class TestRFQLifecycle:
    """End-to-end RFQ lifecycle integration test."""

    def test_complete_rfq_lifecycle(self, client, auth_headers):
        """Test full lifecycle: create -> assign vendors -> publish -> close."""
        # 1. Create vendor
        vendor = _create_vendor(client, auth_headers, name="Lifecycle Vendor")

        # 2. Create RFQ
        rfq = _create_rfq(client, auth_headers, title="Lifecycle Test RFQ")
        assert rfq["status"] == "draft"

        # 3. Update title while in draft
        update_resp = client.put(f"/api/rfqs/{rfq['id']}", headers=auth_headers, json={
            "title": "Updated Lifecycle RFQ",
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "Updated Lifecycle RFQ"

        # 4. Assign vendor
        assign_resp = client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
            "vendor_ids": [vendor["id"]],
        })
        assert assign_resp.status_code == 200

        # 5. Publish
        publish_resp = client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)
        assert publish_resp.status_code == 200
        assert publish_resp.json()["status"] == "open"

        # 6. Verify cannot update after publish
        update_resp = client.put(f"/api/rfqs/{rfq['id']}", headers=auth_headers, json={
            "title": "Shouldn't Work",
        })
        assert update_resp.status_code == 400

        # 7. Close
        close_resp = client.post(f"/api/rfqs/{rfq['id']}/close", headers=auth_headers)
        assert close_resp.status_code == 200
        assert close_resp.json()["status"] == "closed"

        # 8. Verify final state
        detail = client.get(f"/api/rfqs/{rfq['id']}", headers=auth_headers)
        assert detail.json()["status"] == "closed"
        assert detail.json()["vendor_count"] == 1
