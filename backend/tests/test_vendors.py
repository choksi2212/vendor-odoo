"""
Comprehensive vendor management tests for VendorBridge.

Tests cover:
  - Vendor creation (success, validation, duplicate GST)
  - Vendor listing (pagination, search, filters)
  - Vendor retrieval by ID
  - Vendor updates (partial, full, invalid)
  - Vendor deactivation (soft delete)
  - Role-based access control
  - Vendor category CRUD
  - Activity logging verification
"""

import pytest


# ─── Vendor Category Tests ────────────────────────────────────────────────────


class TestVendorCategories:
    """Tests for vendor category endpoints."""

    def test_create_category_success(self, client, auth_headers):
        """Procurement officer can create a category."""
        response = client.post("/api/vendors/categories", headers=auth_headers, json={
            "name": "Electronics",
            "description": "Electronic components and devices",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Electronics"
        assert data["description"] == "Electronic components and devices"
        assert "id" in data

    def test_create_category_admin(self, client, admin_auth_headers):
        """Admin can create a category."""
        response = client.post("/api/vendors/categories", headers=admin_auth_headers, json={
            "name": "Office Supplies",
        })
        assert response.status_code == 201

    def test_create_category_duplicate_name(self, client, auth_headers):
        """Duplicate category name is rejected."""
        client.post("/api/vendors/categories", headers=auth_headers, json={
            "name": "Electronics",
        })
        response = client.post("/api/vendors/categories", headers=auth_headers, json={
            "name": "Electronics",
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_category_vendor_forbidden(self, client, vendor_auth_headers):
        """Vendor cannot create categories."""
        response = client.post("/api/vendors/categories", headers=vendor_auth_headers, json={
            "name": "Test",
        })
        assert response.status_code == 403

    def test_list_categories(self, client, auth_headers):
        """List all categories."""
        # Create some categories
        client.post("/api/vendors/categories", headers=auth_headers, json={"name": "Electronics"})
        client.post("/api/vendors/categories", headers=auth_headers, json={"name": "Furniture"})
        client.post("/api/vendors/categories", headers=auth_headers, json={"name": "IT Equipment"})

        response = client.get("/api/vendors/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Sorted alphabetically
        assert data[0]["name"] == "Electronics"
        assert data[1]["name"] == "Furniture"
        assert data[2]["name"] == "IT Equipment"

    def test_create_category_empty_name(self, client, auth_headers):
        """Category with empty name is rejected."""
        response = client.post("/api/vendors/categories", headers=auth_headers, json={
            "name": "",
        })
        assert response.status_code == 422


# ─── Vendor Creation Tests ────────────────────────────────────────────────────


class TestVendorCreation:
    """Tests for vendor creation endpoint."""

    def test_create_vendor_success(self, client, auth_headers):
        """Procurement officer can create a vendor with valid data."""
        response = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Tech Solutions Pvt Ltd",
            "gst_number": "27AABCU9603R1ZM",
            "email": "contact@techsolutions.com",
            "phone": "+91-9876543210",
            "address": "123 Business Park, Mumbai 400001",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Tech Solutions Pvt Ltd"
        assert data["gst_number"] == "27AABCU9603R1ZM"
        assert data["email"] == "contact@techsolutions.com"
        assert data["phone"] == "+91-9876543210"
        assert data["status"] == "active"
        assert data["rating"] is None
        assert "id" in data
        assert "created_at" in data

    def test_create_vendor_admin(self, client, admin_auth_headers):
        """Admin can create a vendor."""
        response = client.post("/api/vendors", headers=admin_auth_headers, json={
            "name": "Admin Vendor",
            "gst_number": "29AABCU9603R1ZP",
            "email": "admin.vendor@test.com",
        })
        assert response.status_code == 201

    def test_create_vendor_with_category(self, client, auth_headers):
        """Create vendor with assigned category."""
        # Create category first
        cat_response = client.post("/api/vendors/categories", headers=auth_headers, json={
            "name": "Electronics",
        })
        category_id = cat_response.json()["id"]

        # Create vendor with category
        response = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Electronics Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "electronics@vendor.com",
            "category_id": category_id,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == category_id

    def test_create_vendor_invalid_category(self, client, auth_headers):
        """Creating vendor with non-existent category fails."""
        response = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Test Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "test@vendor.com",
            "category_id": "00000000-0000-0000-0000-000000000000",
        })
        assert response.status_code == 404
        assert "category not found" in response.json()["detail"].lower()

    def test_create_vendor_duplicate_gst(self, client, auth_headers):
        """Duplicate GST number is rejected."""
        client.post("/api/vendors", headers=auth_headers, json={
            "name": "Vendor One",
            "gst_number": "27AABCU9603R1ZM",
            "email": "one@vendor.com",
        })
        response = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Vendor Two",
            "gst_number": "27AABCU9603R1ZM",
            "email": "two@vendor.com",
        })
        assert response.status_code == 400
        assert "GST number already exists" in response.json()["detail"]

    def test_create_vendor_invalid_gst_format(self, client, auth_headers):
        """Invalid GST format is rejected."""
        response = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Test Vendor",
            "gst_number": "INVALIDGST12345",
            "email": "test@vendor.com",
        })
        assert response.status_code == 422

    def test_create_vendor_invalid_gst_too_short(self, client, auth_headers):
        """GST number too short is rejected."""
        response = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Test Vendor",
            "gst_number": "27AABCU9603",
            "email": "test@vendor.com",
        })
        assert response.status_code == 422

    def test_create_vendor_invalid_email(self, client, auth_headers):
        """Invalid email is rejected."""
        response = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Test Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "not-valid-email",
        })
        assert response.status_code == 422

    def test_create_vendor_vendor_role_forbidden(self, client, vendor_auth_headers):
        """Vendor role cannot create vendors."""
        response = client.post("/api/vendors", headers=vendor_auth_headers, json={
            "name": "Test Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "test@vendor.com",
        })
        assert response.status_code == 403

    def test_create_vendor_manager_role_forbidden(self, client, manager_auth_headers):
        """Manager role cannot create vendors."""
        response = client.post("/api/vendors", headers=manager_auth_headers, json={
            "name": "Test Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "test@vendor.com",
        })
        assert response.status_code == 403

    def test_create_vendor_no_auth(self, client):
        """Unauthenticated request is rejected."""
        response = client.post("/api/vendors", json={
            "name": "Test Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "test@vendor.com",
        })
        assert response.status_code == 403

    def test_create_vendor_minimal_fields(self, client, auth_headers):
        """Create vendor with only required fields."""
        response = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Minimal Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "minimal@vendor.com",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["phone"] is None
        assert data["address"] is None
        assert data["category_id"] is None


# ─── Vendor Listing Tests ─────────────────────────────────────────────────────


class TestVendorListing:
    """Tests for vendor listing with pagination, search, and filters."""

    def _create_vendors(self, client, auth_headers, count=5):
        """Helper to create multiple vendors."""
        vendors = []
        for i in range(count):
            resp = client.post("/api/vendors", headers=auth_headers, json={
                "name": f"Vendor {chr(65 + i)} Corp",  # Vendor A Corp, B Corp...
                "gst_number": f"27AABCU960{i}R1ZM",
                "email": f"vendor{i}@test.com",
                "phone": f"+91-98765{i:05d}",
            })
            assert resp.status_code == 201
            vendors.append(resp.json())
        return vendors

    def test_list_vendors_empty(self, client, auth_headers):
        """List returns empty when no vendors exist."""
        response = client.get("/api/vendors", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_vendors_pagination(self, client, auth_headers):
        """Pagination works correctly."""
        self._create_vendors(client, auth_headers, count=5)

        # Page 1, size 2
        response = client.get("/api/vendors?page=1&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

        # Page 2
        response = client.get("/api/vendors?page=2&page_size=2", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

        # Page 3 (last page, 1 item)
        response = client.get("/api/vendors?page=3&page_size=2", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 1

    def test_list_vendors_search_by_name(self, client, auth_headers):
        """Search by vendor name."""
        self._create_vendors(client, auth_headers, count=3)

        response = client.get("/api/vendors?search=Vendor A", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Vendor A" in data["items"][0]["name"]

    def test_list_vendors_search_by_email(self, client, auth_headers):
        """Search by vendor email."""
        self._create_vendors(client, auth_headers, count=3)

        response = client.get("/api/vendors?search=vendor2@test.com", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_list_vendors_search_by_gst(self, client, auth_headers):
        """Search by GST number."""
        self._create_vendors(client, auth_headers, count=3)

        response = client.get("/api/vendors?search=27AABCU9601R1ZM", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_list_vendors_filter_by_status(self, client, auth_headers):
        """Filter vendors by status."""
        vendors = self._create_vendors(client, auth_headers, count=3)

        # Deactivate one vendor
        client.delete(f"/api/vendors/{vendors[0]['id']}", headers=auth_headers)

        # Filter active only
        response = client.get("/api/vendors?status=active", headers=auth_headers)
        data = response.json()
        assert data["total"] == 2

        # Filter inactive only
        response = client.get("/api/vendors?status=inactive", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1

    def test_list_vendors_filter_by_category(self, client, auth_headers):
        """Filter vendors by category."""
        # Create categories
        cat1 = client.post("/api/vendors/categories", headers=auth_headers, json={
            "name": "Electronics"
        }).json()
        cat2 = client.post("/api/vendors/categories", headers=auth_headers, json={
            "name": "Furniture"
        }).json()

        # Create vendors in different categories
        client.post("/api/vendors", headers=auth_headers, json={
            "name": "Elec Vendor", "gst_number": "27AABCU9600R1ZM",
            "email": "e1@v.com", "category_id": cat1["id"],
        })
        client.post("/api/vendors", headers=auth_headers, json={
            "name": "Furn Vendor", "gst_number": "27AABCU9601R1ZM",
            "email": "f1@v.com", "category_id": cat2["id"],
        })

        # Filter by electronics
        response = client.get(f"/api/vendors?category_id={cat1['id']}", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Elec Vendor"

    def test_list_vendors_vendor_role_forbidden(self, client, vendor_auth_headers):
        """Vendor role cannot list vendors."""
        response = client.get("/api/vendors", headers=vendor_auth_headers)
        assert response.status_code == 403

    def test_list_vendors_manager_allowed(self, client, manager_auth_headers):
        """Manager can list vendors."""
        response = client.get("/api/vendors", headers=manager_auth_headers)
        assert response.status_code == 200


# ─── Vendor Get By ID Tests ───────────────────────────────────────────────────


class TestVendorGetById:
    """Tests for getting a vendor by ID."""

    def test_get_vendor_success(self, client, auth_headers):
        """Get vendor by valid ID."""
        create_resp = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Test Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "test@vendor.com",
        })
        vendor_id = create_resp.json()["id"]

        response = client.get(f"/api/vendors/{vendor_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == vendor_id
        assert data["name"] == "Test Vendor"

    def test_get_vendor_not_found(self, client, auth_headers):
        """Get vendor with non-existent ID returns 404."""
        response = client.get(
            "/api/vendors/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_vendor_manager_allowed(self, client, auth_headers, manager_auth_headers):
        """Manager can view vendors."""
        create_resp = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Test Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "test@vendor.com",
        })
        vendor_id = create_resp.json()["id"]

        response = client.get(f"/api/vendors/{vendor_id}", headers=manager_auth_headers)
        assert response.status_code == 200


# ─── Vendor Update Tests ──────────────────────────────────────────────────────


class TestVendorUpdate:
    """Tests for updating vendor details."""

    def _create_vendor(self, client, auth_headers):
        resp = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Original Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "original@vendor.com",
            "phone": "+91-9876543210",
            "address": "Original Address",
        })
        return resp.json()

    def test_update_vendor_name(self, client, auth_headers):
        """Update vendor name."""
        vendor = self._create_vendor(client, auth_headers)

        response = client.put(f"/api/vendors/{vendor['id']}", headers=auth_headers, json={
            "name": "Updated Vendor Name",
        })
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Vendor Name"

    def test_update_vendor_email(self, client, auth_headers):
        """Update vendor email."""
        vendor = self._create_vendor(client, auth_headers)

        response = client.put(f"/api/vendors/{vendor['id']}", headers=auth_headers, json={
            "email": "updated@vendor.com",
        })
        assert response.status_code == 200
        assert response.json()["email"] == "updated@vendor.com"

    def test_update_vendor_multiple_fields(self, client, auth_headers):
        """Update multiple fields at once."""
        vendor = self._create_vendor(client, auth_headers)

        response = client.put(f"/api/vendors/{vendor['id']}", headers=auth_headers, json={
            "name": "New Name",
            "phone": "+91-1111111111",
            "address": "New Address, New City",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["phone"] == "+91-1111111111"
        assert data["address"] == "New Address, New City"

    def test_update_vendor_status_to_inactive(self, client, auth_headers):
        """Update vendor status to inactive."""
        vendor = self._create_vendor(client, auth_headers)

        response = client.put(f"/api/vendors/{vendor['id']}", headers=auth_headers, json={
            "status": "inactive",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "inactive"

    def test_update_vendor_invalid_status(self, client, auth_headers):
        """Invalid status value is rejected."""
        vendor = self._create_vendor(client, auth_headers)

        response = client.put(f"/api/vendors/{vendor['id']}", headers=auth_headers, json={
            "status": "suspended",
        })
        assert response.status_code == 422

    def test_update_vendor_not_found(self, client, auth_headers):
        """Update non-existent vendor returns 404."""
        response = client.put(
            "/api/vendors/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
            json={"name": "Test"},
        )
        assert response.status_code == 404

    def test_update_vendor_vendor_role_forbidden(self, client, auth_headers, vendor_auth_headers):
        """Vendor cannot update vendors."""
        vendor = self._create_vendor(client, auth_headers)

        response = client.put(
            f"/api/vendors/{vendor['id']}",
            headers=vendor_auth_headers,
            json={"name": "Hacked"},
        )
        assert response.status_code == 403


# ─── Vendor Deactivation Tests ────────────────────────────────────────────────


class TestVendorDeactivation:
    """Tests for vendor soft delete (deactivation)."""

    def _create_vendor(self, client, auth_headers):
        resp = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Deletable Vendor",
            "gst_number": "27AABCU9603R1ZM",
            "email": "delete@vendor.com",
        })
        return resp.json()

    def test_deactivate_vendor_success(self, client, auth_headers):
        """Deactivate a vendor (soft delete)."""
        vendor = self._create_vendor(client, auth_headers)

        response = client.delete(f"/api/vendors/{vendor['id']}", headers=auth_headers)
        assert response.status_code == 204

        # Verify status is now inactive
        get_resp = client.get(f"/api/vendors/{vendor['id']}", headers=auth_headers)
        assert get_resp.json()["status"] == "inactive"

    def test_deactivate_already_inactive(self, client, auth_headers):
        """Deactivating an already inactive vendor returns error."""
        vendor = self._create_vendor(client, auth_headers)
        client.delete(f"/api/vendors/{vendor['id']}", headers=auth_headers)

        # Try to deactivate again
        response = client.delete(f"/api/vendors/{vendor['id']}", headers=auth_headers)
        assert response.status_code == 400
        assert "already inactive" in response.json()["detail"].lower()

    def test_deactivate_vendor_not_found(self, client, auth_headers):
        """Deactivating non-existent vendor returns 404."""
        response = client.delete(
            "/api/vendors/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_deactivate_vendor_vendor_role_forbidden(self, client, auth_headers, vendor_auth_headers):
        """Vendor role cannot deactivate vendors."""
        vendor = self._create_vendor(client, auth_headers)

        response = client.delete(
            f"/api/vendors/{vendor['id']}",
            headers=vendor_auth_headers,
        )
        assert response.status_code == 403
