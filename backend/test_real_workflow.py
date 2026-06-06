"""
Full procurement workflow test against REAL PostgreSQL database.
Tests the complete 8-step flow: RFQ -> Quotation -> Approval -> PO -> Invoice -> PDF
"""

import httpx
import sys

BASE = "http://localhost:8000"

def main():
    print("=" * 70)
    print("VENDORBRIDGE - FULL PROCUREMENT WORKFLOW TEST (Real PostgreSQL)")
    print("=" * 70)
    print()

    # === 1. LOGIN AS OFFICER ===
    print("STEP 1: Login as Procurement Officer")
    r = httpx.post(f"{BASE}/api/auth/login", json={
        "email": "officer@vendorbridge.com", "password": "Officer123!"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    officer_token = r.json()["access_token"]
    OH = {"Authorization": f"Bearer {officer_token}"}
    print(f"  [OK] Logged in. Token: {officer_token[:20]}...")
    print()

    # === 2. GET PROFILE ===
    print("STEP 2: Verify profile")
    r = httpx.get(f"{BASE}/api/users/me", headers=OH)
    assert r.status_code == 200
    user = r.json()
    print(f"  [OK] Email: {user['email']} | Role: {user['role']}")
    print()

    # === 3. CREATE VENDOR ===
    print("STEP 3: Create Vendor Category + Vendor")
    r = httpx.post(f"{BASE}/api/vendors/categories", headers=OH, json={
        "name": "Electronics", "description": "Electronic hardware vendors"
    })
    cat_id = r.json()["id"]
    print(f"  [OK] Category created: Electronics (ID: {cat_id})")

    r = httpx.post(f"{BASE}/api/vendors", headers=OH, json={
        "name": "Acme Industrial Supplies",
        "gst_number": "29AABCU9603R1ZP",
        "email": "sales@acmeindustrial.com",
        "phone": "+91-8765432109",
        "address": "789 Industrial Zone, Pune 411001",
        "category_id": cat_id,
    })
    assert r.status_code == 201, f"Vendor creation failed: {r.text}"
    vendor = r.json()
    print(f"  [OK] Vendor created: {vendor['name']} | GST: {vendor['gst_number']}")
    print()

    # === 4. CREATE RFQ ===
    print("STEP 4: Create RFQ")
    r = httpx.post(f"{BASE}/api/rfqs", headers=OH, json={
        "title": "Annual Office Laptop Refresh Program",
        "description": "80 developer-grade laptops with 3-year warranty for engineering team",
        "product_name": "Dell XPS 15 (i7, 32GB, 1TB SSD)",
        "quantity": 80,
        "unit": "units",
        "deadline": "2026-07-20",
    })
    assert r.status_code == 201, f"RFQ creation failed: {r.text}"
    rfq = r.json()
    print(f"  [OK] RFQ created: {rfq['title']}")
    print(f"       Status: {rfq['status']} | Qty: {rfq['quantity']} {rfq['unit']}")
    print()

    # === 5. ASSIGN VENDOR + PUBLISH ===
    print("STEP 5: Assign Vendor and Publish RFQ")
    r = httpx.post(f"{BASE}/api/rfqs/{rfq['id']}/assign-vendors", headers=OH, json={
        "vendor_ids": [vendor["id"]]
    })
    assert r.status_code == 200
    print(f"  [OK] Vendor assigned: {vendor['name']}")

    r = httpx.post(f"{BASE}/api/rfqs/{rfq['id']}/publish", headers=OH)
    assert r.status_code == 200
    print(f"  [OK] RFQ published. Status: {r.json()['status']}")
    print()

    # === 6. SUBMIT QUOTATION ===
    print("STEP 6: Vendor submits quotation")
    r = httpx.post(f"{BASE}/api/quotations", headers=OH, json={
        "rfq_id": rfq["id"],
        "vendor_id": vendor["id"],
        "unit_price": "92500.00",
        "delivery_days": 21,
        "notes": "Pre-configured with dev tools. On-site deployment support included.",
    })
    assert r.status_code == 201, f"Quotation creation failed: {r.text}"
    quotation = r.json()
    print(f"  [OK] Quotation created: Rs.{quotation['unit_price']}/unit")
    print(f"       Total: Rs.{quotation['total_price']} | Delivery: {quotation['delivery_days']} days")

    r = httpx.post(f"{BASE}/api/quotations/{quotation['id']}/submit", headers=OH)
    assert r.status_code == 200
    print(f"  [OK] Quotation submitted. Status: {r.json()['status']}")
    print()

    # === 7. REQUEST APPROVAL ===
    print("STEP 7: Request approval from manager")
    r = httpx.post(f"{BASE}/api/approvals", headers=OH, json={
        "rfq_id": rfq["id"],
        "quotation_id": quotation["id"],
    })
    assert r.status_code == 201, f"Approval creation failed: {r.text}"
    approval = r.json()
    print(f"  [OK] Approval requested. Status: {approval['status']}")
    print(f"       Vendor: {approval['vendor_name']} | Amount: Rs.{approval['total_amount']}")
    print()

    # === 8. MANAGER APPROVES ===
    print("STEP 8: Manager logs in and approves")
    r = httpx.post(f"{BASE}/api/auth/login", json={
        "email": "manager@vendorbridge.com", "password": "Manager123!"
    })
    assert r.status_code == 200
    manager_token = r.json()["access_token"]
    MH = {"Authorization": f"Bearer {manager_token}"}
    print(f"  [OK] Manager logged in")

    r = httpx.post(f"{BASE}/api/approvals/{approval['id']}/approve", headers=MH, json={
        "remarks": "Good price for dev-grade laptops. Approved for procurement."
    })
    assert r.status_code == 200
    print(f"  [OK] Approval APPROVED. Remarks: {r.json()['remarks']}")
    print()

    # === 9. GENERATE PURCHASE ORDER ===
    print("STEP 9: Generate Purchase Order")
    r = httpx.post(f"{BASE}/api/purchase-orders", headers=OH, json={
        "approval_id": approval["id"],
        "notes": "Delivery to HQ Building A, Floor 3. Contact: IT Dept.",
    })
    assert r.status_code == 201, f"PO creation failed: {r.text}"
    po = r.json()
    print(f"  [OK] PO Generated: {po['po_number']}")
    print(f"       Subtotal: Rs.{po['subtotal']}")
    print(f"       Tax ({po['tax_rate']}% GST): Rs.{po['tax_amount']}")
    print(f"       TOTAL: Rs.{po['total_amount']}")
    print(f"       Line Items: {len(po['line_items'])}")
    for li in po["line_items"]:
        print(f"         - {li['product_name']} x{li['quantity']} @ Rs.{li['unit_price']}")
    print()

    # === 10. GENERATE INVOICE ===
    print("STEP 10: Generate Invoice from PO")
    r = httpx.post(f"{BASE}/api/invoices", headers=OH, json={
        "purchase_order_id": po["id"],
        "notes": "Payment terms: Net 30 days. Bank transfer preferred.",
    })
    assert r.status_code == 201, f"Invoice creation failed: {r.text}"
    invoice = r.json()
    print(f"  [OK] Invoice Generated: {invoice['invoice_number']}")
    print(f"       PO Ref: {invoice['po_number']}")
    print(f"       Vendor: {invoice['vendor_name']}")
    print(f"       Total: Rs.{invoice['total_amount']}")
    print(f"       Status: {invoice['status']}")
    print()

    # === 11. DOWNLOAD PDF ===
    print("STEP 11: Generate and Download Invoice PDF")
    r = httpx.get(f"{BASE}/api/invoices/{invoice['id']}/pdf", headers=OH)
    assert r.status_code == 200, f"PDF download failed: {r.status_code}"
    pdf_size = len(r.content)
    assert r.content[:4] == b"%PDF", "Response is not a valid PDF!"
    print(f"  [OK] PDF Downloaded: {pdf_size:,} bytes")
    print(f"       Valid PDF: Yes (starts with %PDF)")
    print()

    # === 12. MARK INVOICE ISSUED AND PAID ===
    print("STEP 12: Issue and mark invoice as paid")
    r = httpx.post(f"{BASE}/api/invoices/{invoice['id']}/issue", headers=OH)
    assert r.status_code == 200
    print(f"  [OK] Invoice issued. Status: {r.json()['status']}")

    r = httpx.post(f"{BASE}/api/invoices/{invoice['id']}/mark-paid", headers=OH)
    assert r.status_code == 200
    print(f"  [OK] Invoice PAID. Paid at: {r.json()['paid_at']}")
    print()

    # === 13. CHECK ANALYTICS ===
    print("STEP 13: Check Dashboard Analytics")
    r = httpx.get(f"{BASE}/api/analytics/dashboard", headers=OH)
    assert r.status_code == 200
    stats = r.json()
    print(f"  [OK] Dashboard Stats:")
    print(f"       Active RFQs: {stats['active_rfqs']}")
    print(f"       Total Vendors: {stats['total_vendors']}")
    print(f"       POs This Month: {stats['total_pos_this_month']}")
    print(f"       Invoices This Month: {stats['total_invoices_this_month']}")
    print(f"       Monthly Spend: Rs.{stats['total_spend_this_month']}")
    print(f"       Yearly Spend: Rs.{stats['total_spend_this_year']}")
    print()

    # === 14. VERIFY IN DATABASE ===
    print("STEP 14: Verify data in PostgreSQL")
    r = httpx.get(f"{BASE}/api/vendors", headers=OH)
    print(f"  Vendors in DB: {r.json()['total']}")
    r = httpx.get(f"{BASE}/api/rfqs", headers=OH)
    print(f"  RFQs in DB: {r.json()['total']}")
    r = httpx.get(f"{BASE}/api/purchase-orders", headers=OH)
    print(f"  POs in DB: {r.json()['total']}")
    r = httpx.get(f"{BASE}/api/invoices", headers=OH)
    print(f"  Invoices in DB: {r.json()['total']}")
    print()

    print("=" * 70)
    print("ALL 14 STEPS PASSED - COMPLETE WORKFLOW VERIFIED ON REAL POSTGRESQL!")
    print("=" * 70)


if __name__ == "__main__":
    main()
