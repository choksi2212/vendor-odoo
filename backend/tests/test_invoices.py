"""
Comprehensive invoice and PDF generation tests for VendorBridge.

Tests cover:
  - Invoice creation from PO (success, validations)
  - Sequential invoice numbering (INV-YYYY-XXXX)
  - Line items copied from PO
  - Amount verification (subtotal, tax, total)
  - PDF generation (actual ReportLab output)
  - Invoice status workflow (draft -> issued -> paid)
  - Mark paid updates PO status
  - Duplicate invoice prevention
  - Role-based access control
  - Invoice listing with filters
"""

from datetime import date, timedelta
from decimal import Decimal


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _future_date(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


def _create_po(client, auth_headers, manager_auth_headers, quantity=100, unit_price="200.00"):
    """Create the full chain up to a Purchase Order."""
    # Vendor
    v_resp = client.post("/api/vendors", headers=auth_headers, json={
        "name": "Invoice Test Vendor",
        "gst_number": "27AABCU9600R1ZM",
        "email": "invoice.vendor@test.com",
        "address": "456 Industrial Area, Chennai 600001",
    })
    vendor = v_resp.json()

    # RFQ
    rfq_resp = client.post("/api/rfqs", headers=auth_headers, json={
        "title": "Invoice Test RFQ",
        "product_name": "Server Rack",
        "quantity": quantity,
        "unit": "units",
        "deadline": _future_date(30),
    })
    rfq = rfq_resp.json()
    client.post(f"/api/rfqs/{rfq['id']}/assign-vendors", headers=auth_headers, json={
        "vendor_ids": [vendor["id"]],
    })
    client.post(f"/api/rfqs/{rfq['id']}/publish", headers=auth_headers)

    # Quotation
    q_resp = client.post("/api/quotations", headers=auth_headers, json={
        "rfq_id": rfq["id"],
        "vendor_id": vendor["id"],
        "unit_price": unit_price,
        "delivery_days": 14,
    })
    quotation = q_resp.json()
    client.post(f"/api/quotations/{quotation['id']}/submit", headers=auth_headers)

    # Approval
    a_resp = client.post("/api/approvals", headers=auth_headers, json={
        "rfq_id": rfq["id"],
        "quotation_id": quotation["id"],
    })
    approval = a_resp.json()
    client.post(f"/api/approvals/{approval['id']}/approve", headers=manager_auth_headers, json={})

    # PO
    po_resp = client.post("/api/purchase-orders", headers=auth_headers, json={
        "approval_id": approval["id"],
    })
    return po_resp.json()


# ─── Invoice Creation Tests ───────────────────────────────────────────────────


class TestInvoiceCreation:
    """Tests for invoice creation from PO."""

    def test_create_invoice_success(self, client, auth_headers, manager_auth_headers):
        """Create invoice from a PO with correct data."""
        po = _create_po(client, auth_headers, manager_auth_headers, quantity=10, unit_price="500.00")

        response = client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po["id"],
            "notes": "Net 30 days payment terms.",
        })
        assert response.status_code == 201
        data = response.json()

        # Verify invoice number format
        assert data["invoice_number"].startswith("INV-")
        parts = data["invoice_number"].split("-")
        assert len(parts) == 3

        # Verify amounts match PO
        assert Decimal(data["subtotal"]) == Decimal("5000.00")  # 500 * 10
        assert Decimal(data["tax_rate"]) == Decimal("18.00")
        assert Decimal(data["tax_amount"]) == Decimal("900.00")
        assert Decimal(data["total_amount"]) == Decimal("5900.00")

        # Verify metadata
        assert data["status"] == "draft"
        assert data["vendor_name"] == "Invoice Test Vendor"
        assert data["po_number"] == po["po_number"]
        assert data["notes"] == "Net 30 days payment terms."

        # Verify line items
        assert len(data["line_items"]) == 1
        li = data["line_items"][0]
        assert li["product_name"] == "Server Rack"
        assert li["quantity"] == 10
        assert li["unit"] == "units"
        assert Decimal(li["unit_price"]) == Decimal("500.00")
        assert Decimal(li["total_price"]) == Decimal("5000.00")

    def test_create_invoice_sequential_numbering(self, client, auth_headers, manager_auth_headers):
        """Invoice numbers are sequential."""
        po1 = _create_po(client, auth_headers, manager_auth_headers, quantity=5, unit_price="100.00")
        resp1 = client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po1["id"],
        })
        inv1 = resp1.json()

        # Create second chain for second invoice
        v2_resp = client.post("/api/vendors", headers=auth_headers, json={
            "name": "Second Vendor", "gst_number": "27AABCU9601R1ZM", "email": "v2@t.com",
        })
        v2 = v2_resp.json()
        rfq2_resp = client.post("/api/rfqs", headers=auth_headers, json={
            "title": "RFQ 2", "product_name": "Item 2",
            "quantity": 20, "unit": "pc", "deadline": _future_date(30),
        })
        rfq2 = rfq2_resp.json()
        client.post(f"/api/rfqs/{rfq2['id']}/assign-vendors", headers=auth_headers, json={"vendor_ids": [v2["id"]]})
        client.post(f"/api/rfqs/{rfq2['id']}/publish", headers=auth_headers)
        q2_resp = client.post("/api/quotations", headers=auth_headers, json={
            "rfq_id": rfq2["id"], "vendor_id": v2["id"], "unit_price": "75.00", "delivery_days": 7,
        })
        q2 = q2_resp.json()
        client.post(f"/api/quotations/{q2['id']}/submit", headers=auth_headers)
        a2_resp = client.post("/api/approvals", headers=auth_headers, json={
            "rfq_id": rfq2["id"], "quotation_id": q2["id"],
        })
        a2 = a2_resp.json()
        client.post(f"/api/approvals/{a2['id']}/approve", headers=manager_auth_headers, json={})
        po2_resp = client.post("/api/purchase-orders", headers=auth_headers, json={"approval_id": a2["id"]})
        po2 = po2_resp.json()

        resp2 = client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po2["id"],
        })
        inv2 = resp2.json()

        # Sequential check
        num1 = int(inv1["invoice_number"].split("-")[-1])
        num2 = int(inv2["invoice_number"].split("-")[-1])
        assert num2 == num1 + 1

    def test_create_invoice_po_not_found(self, client, auth_headers):
        """Cannot create invoice for non-existent PO."""
        response = client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": "00000000-0000-0000-0000-000000000000",
        })
        assert response.status_code == 404

    def test_create_invoice_duplicate_rejected(self, client, auth_headers, manager_auth_headers):
        """Cannot create two invoices for the same PO."""
        po = _create_po(client, auth_headers, manager_auth_headers)
        client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po["id"],
        })

        response = client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po["id"],
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_create_invoice_vendor_forbidden(self, client, auth_headers, manager_auth_headers, vendor_auth_headers):
        """Vendor cannot create invoices."""
        po = _create_po(client, auth_headers, manager_auth_headers)
        response = client.post("/api/invoices", headers=vendor_auth_headers, json={
            "purchase_order_id": po["id"],
        })
        assert response.status_code == 403


# ─── PDF Generation Tests ─────────────────────────────────────────────────────


class TestPDFGeneration:
    """Tests for invoice PDF generation."""

    def test_generate_pdf_success(self, client, auth_headers, manager_auth_headers):
        """PDF is generated and returned as bytes."""
        po = _create_po(client, auth_headers, manager_auth_headers, quantity=5, unit_price="1000.00")
        inv_resp = client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po["id"],
            "notes": "Payment due within 30 days.",
        })
        invoice = inv_resp.json()

        response = client.get(f"/api/invoices/{invoice['id']}/pdf", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert invoice["invoice_number"] in response.headers["content-disposition"]

        # Verify it's actual PDF content (starts with %PDF)
        assert response.content[:4] == b"%PDF"
        assert len(response.content) > 1000  # Reasonable PDF size

    def test_generate_pdf_not_found(self, client, auth_headers):
        """PDF generation for non-existent invoice returns 404."""
        response = client.get(
            "/api/invoices/00000000-0000-0000-0000-000000000000/pdf",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ─── Invoice Status Workflow Tests ────────────────────────────────────────────


class TestInvoiceStatusWorkflow:
    """Tests for invoice status transitions."""

    def _create_invoice(self, client, auth_headers, manager_auth_headers):
        po = _create_po(client, auth_headers, manager_auth_headers)
        resp = client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po["id"],
        })
        return resp.json(), po

    def test_issue_invoice(self, client, auth_headers, manager_auth_headers):
        """Transition draft -> issued."""
        invoice, _ = self._create_invoice(client, auth_headers, manager_auth_headers)

        response = client.post(f"/api/invoices/{invoice['id']}/issue", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "issued"

    def test_issue_already_issued_rejected(self, client, auth_headers, manager_auth_headers):
        """Cannot issue an already issued invoice."""
        invoice, _ = self._create_invoice(client, auth_headers, manager_auth_headers)
        client.post(f"/api/invoices/{invoice['id']}/issue", headers=auth_headers)

        response = client.post(f"/api/invoices/{invoice['id']}/issue", headers=auth_headers)
        assert response.status_code == 400

    def test_mark_paid_success(self, client, auth_headers, manager_auth_headers):
        """Transition issued -> paid."""
        invoice, _ = self._create_invoice(client, auth_headers, manager_auth_headers)
        client.post(f"/api/invoices/{invoice['id']}/issue", headers=auth_headers)

        response = client.post(f"/api/invoices/{invoice['id']}/mark-paid", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"
        assert data["paid_at"] is not None

    def test_mark_paid_draft_rejected(self, client, auth_headers, manager_auth_headers):
        """Cannot mark draft invoice as paid (must issue first)."""
        invoice, _ = self._create_invoice(client, auth_headers, manager_auth_headers)

        response = client.post(f"/api/invoices/{invoice['id']}/mark-paid", headers=auth_headers)
        assert response.status_code == 400
        assert "issued" in response.json()["detail"].lower()

    def test_mark_paid_updates_po_status(self, client, auth_headers, manager_auth_headers):
        """Marking invoice paid also updates PO to paid."""
        invoice, po = self._create_invoice(client, auth_headers, manager_auth_headers)
        client.post(f"/api/invoices/{invoice['id']}/issue", headers=auth_headers)
        client.post(f"/api/invoices/{invoice['id']}/mark-paid", headers=auth_headers)

        # Check PO status
        po_resp = client.get(f"/api/purchase-orders/{po['id']}", headers=auth_headers)
        assert po_resp.json()["status"] == "paid"


# ─── Invoice Listing Tests ────────────────────────────────────────────────────


class TestInvoiceListing:
    """Tests for invoice listing."""

    def test_list_invoices_empty(self, client, auth_headers):
        """List returns empty."""
        response = client.get("/api/invoices", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_invoices_with_data(self, client, auth_headers, manager_auth_headers):
        """List returns invoices with line items."""
        po = _create_po(client, auth_headers, manager_auth_headers)
        client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po["id"],
        })

        response = client.get("/api/invoices", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"][0]["line_items"]) == 1

    def test_list_invoices_filter_by_status(self, client, auth_headers, manager_auth_headers):
        """Filter invoices by status."""
        po = _create_po(client, auth_headers, manager_auth_headers)
        inv_resp = client.post("/api/invoices", headers=auth_headers, json={
            "purchase_order_id": po["id"],
        })
        invoice = inv_resp.json()
        client.post(f"/api/invoices/{invoice['id']}/issue", headers=auth_headers)

        # Filter draft (0)
        response = client.get("/api/invoices?status=draft", headers=auth_headers)
        assert response.json()["total"] == 0

        # Filter issued (1)
        response = client.get("/api/invoices?status=issued", headers=auth_headers)
        assert response.json()["total"] == 1

    def test_list_invoices_vendor_forbidden(self, client, vendor_auth_headers):
        """Vendor cannot list invoices."""
        response = client.get("/api/invoices", headers=vendor_auth_headers)
        assert response.status_code == 403
