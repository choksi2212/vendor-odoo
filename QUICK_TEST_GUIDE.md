# Quick Test Guide - Vendor Functionality

## Prerequisites
- Backend server running on `http://localhost:8000`
- Frontend running on `http://localhost:5173` (or your dev port)
- PostgreSQL database connected
- `BREVO_API_KEY` configured in `.env` for email notifications

## Step-by-Step Test

### Step 1: Create Vendor Entity (As Procurement Officer)

Login as procurement officer, then:

**UI Method:**
1. Go to "Vendors" in sidebar
2. Click "+ Add Vendor"
3. Fill in:
   - Name: `Test Vendor Company`
   - Email: `vendor@test.com` ⚠️ **Remember this email!**
   - GST: `29TEST1234X1ZX`
   - Phone: `+91-9876543210`
   - Address: `123 Test Street`
4. Click "Add Vendor"

**API Method:**
```bash
curl -X POST http://localhost:8000/api/vendors \
  -H "Authorization: Bearer YOUR_OFFICER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Vendor Company",
    "email": "vendor@test.com",
    "gst_number": "29TEST1234X1ZX",
    "phone": "+91-9876543210",
    "address": "123 Test Street"
  }'
```

---

### Step 2: Create Vendor User Account

Go to signup page or use API:

```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vendor@test.com",
    "password": "VendorPass123!",
    "role": "vendor",
    "username": "testvendor"
  }'
```

⚠️ **Email must match the vendor entity email exactly!**

---

### Step 3: Verify Email (if required)

Check your email for verification link or skip if email verification is disabled.

---

### Step 4: Login as Vendor User

**UI Method:**
1. Go to login page
2. Email: `vendor@test.com`
3. Password: `VendorPass123!`
4. Click Login

**API Method:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vendor@test.com",
    "password": "VendorPass123!"
  }'
```

Save the `access_token` from response.

---

### Step 5: Verify Vendor Linking

```bash
curl -X GET http://localhost:8000/api/users/me/vendor-profile \
  -H "Authorization: Bearer YOUR_VENDOR_TOKEN"
```

**Expected Response:**
```json
{
  "is_vendor_user": true,
  "has_vendor_entity": true,
  "vendor_id": "some-uuid",
  "vendor_name": "Test Vendor Company",
  "vendor_email": "vendor@test.com",
  "vendor_status": "active",
  "message": "Vendor profile linked successfully"
}
```

✅ If `has_vendor_entity: true` → **LINKING SUCCESSFUL!**  
❌ If `has_vendor_entity: false` → **Email mismatch - check Step 1 & 2**

---

### Step 6: Create and Publish RFQ (As Procurement Officer)

Switch back to procurement officer account:

**UI Method:**
1. Go to "RFQs" page
2. Click "+ Create RFQ"
3. Fill in:
   - Title: `Test RFQ for Vendor`
   - Product: `Test Product`
   - Quantity: `10`
   - Unit: `units`
   - Deadline: Select future date
4. **Important:** Check the "Test Vendor Company" in vendor list
5. Click "Submit RFQ"
6. On RFQ detail page, click "Publish RFQ"

**API Method:**
```bash
# 1. Create RFQ
curl -X POST http://localhost:8000/api/rfqs \
  -H "Authorization: Bearer YOUR_OFFICER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test RFQ for Vendor",
    "description": "Testing vendor functionality",
    "product_name": "Test Product",
    "quantity": 10,
    "unit": "units",
    "deadline": "2026-12-31"
  }'

# Save RFQ ID from response

# 2. Assign Vendor
curl -X POST http://localhost:8000/api/rfqs/{RFQ_ID}/assign-vendors \
  -H "Authorization: Bearer YOUR_OFFICER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_ids": ["VENDOR_ID_FROM_STEP1"]
  }'

# 3. Publish (sends email)
curl -X POST http://localhost:8000/api/rfqs/{RFQ_ID}/publish \
  -H "Authorization: Bearer YOUR_OFFICER_TOKEN"
```

📧 **Check email!** Vendor should receive invitation email.

---

### Step 7: View RFQ as Vendor

Login as vendor user (`vendor@test.com`) and:

**Dashboard:**
- Should load without errors ✅
- Should show "RFQs Assigned to You" section ✅
- Should show 1 RFQ in the list ✅

**RFQs Page:**
1. Click "RFQs" in sidebar
2. Should see "Test RFQ for Vendor" ✅
3. Status should be "open" ✅
4. Should NOT see "Create RFQ" button ✅

---

### Step 8: Submit Quotation as Vendor

**UI Method:**
1. Click on the RFQ from list
2. Click "Submit Quote" button
3. Fill in:
   - Unit Price: `1500.00`
   - Delivery Days: `15`
   - Notes: `High quality materials`
4. Click "Submit Quotation"

**API Method:**
```bash
curl -X POST http://localhost:8000/api/quotations \
  -H "Authorization: Bearer YOUR_VENDOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rfq_id": "RFQ_ID",
    "vendor_id": "VENDOR_ID",
    "unit_price": "1500.00",
    "delivery_days": 15,
    "notes": "High quality materials"
  }'

# Save quotation ID

# Submit the quotation
curl -X POST http://localhost:8000/api/quotations/{QUOTATION_ID}/submit \
  -H "Authorization: Bearer YOUR_VENDOR_TOKEN"
```

---

### Step 9: View "My Quotations"

Still logged in as vendor:

1. Click "My Quotations" in sidebar
2. Should see the quotation you just created ✅
3. Should show:
   - RFQ title: "Test RFQ for Vendor"
   - Status: "submitted"
   - Price: ₹1,500
   - Delivery: 15 days

**API Method:**
```bash
curl -X GET http://localhost:8000/api/quotations \
  -H "Authorization: Bearer YOUR_VENDOR_TOKEN"
```

---

## Testing Checklist

### Vendor Dashboard
- [ ] Dashboard loads without "Access denied" error
- [ ] Shows vendor-specific view (not procurement officer view)
- [ ] Shows "RFQs Assigned to You" section
- [ ] Shows correct RFQ count
- [ ] No analytics stats visible (that's for officers only)

### RFQ Functionality
- [ ] RFQs page loads successfully
- [ ] Shows only RFQs assigned to this vendor
- [ ] Shows only "open" status RFQs
- [ ] Status filter works (draft/open/closed)
- [ ] Search functionality works
- [ ] "Create RFQ" button is hidden for vendors
- [ ] Clicking RFQ opens detail page

### Quotation Functionality
- [ ] "My Quotations" page loads (no "Method Not Allowed")
- [ ] Shows only this vendor's quotations
- [ ] Can create draft quotation
- [ ] Can submit quotation
- [ ] RFQ title appears correctly
- [ ] Unit price and delivery days display correctly

### Email Notifications
- [ ] Email received when RFQ published
- [ ] Email contains RFQ details
- [ ] Email link works
- [ ] Email is professionally formatted

### Security & Restrictions
- [ ] Cannot access vendor list page
- [ ] Cannot access analytics page
- [ ] Cannot access reports page
- [ ] Cannot see other vendors' quotations
- [ ] Cannot create/edit/delete RFQs
- [ ] Cannot approve quotations

---

## Troubleshooting

### Problem: "No RFQs yet" message

**Causes:**
1. Vendor not linked to entity (email mismatch)
2. No RFQs published for this vendor
3. RFQ status is not "open"

**Solutions:**
1. Check `/api/users/me/vendor-profile` - must show `has_vendor_entity: true`
2. Ensure RFQ is published (not draft)
3. Ensure vendor is assigned to RFQ

---

### Problem: "My Quotations" shows empty

**Causes:**
1. Vendor not linked to entity
2. No quotations created yet

**Solutions:**
1. Check vendor-profile endpoint
2. Create and submit a quotation

---

### Problem: Email not received

**Causes:**
1. `BREVO_API_KEY` not configured
2. Vendor email invalid
3. Email in spam folder

**Solutions:**
1. Check `.env` file has `BREVO_API_KEY`
2. Check backend logs for email errors
3. Check spam/junk folder
4. Verify email address is correct

---

### Problem: "Access denied" on dashboard

**Cause:** Analytics API call failing (should be fixed)

**Solution:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Check browser console for errors

---

## API Endpoints Summary

### Vendor-Specific Endpoints
```
GET  /api/users/me/vendor-profile     # Check linking
GET  /api/rfqs                         # List assigned RFQs
GET  /api/quotations                   # List my quotations
POST /api/quotations                   # Create quotation
POST /api/quotations/{id}/submit      # Submit quotation
GET  /api/quotations/{id}             # Get quotation details
```

### All Users
```
GET  /api/users/me                    # Get profile
POST /api/auth/login                  # Login
POST /api/auth/logout                 # Logout
```

---

## Expected Behavior vs Issues

| Feature | Expected | Old Issue | Status |
|---------|----------|-----------|--------|
| Dashboard | Loads for vendors | Access denied | ✅ Fixed |
| My Quotations | Shows vendor quotations | Method Not Allowed | ✅ Fixed |
| RFQ List | Shows assigned RFQs | Empty list | ✅ Fixed |
| Create RFQ | Hidden for vendors | Visible | ✅ Fixed |
| Email | Sent on publish | Not sent | ✅ Fixed |
| Status Filter | "open" option | "published" (wrong) | ✅ Fixed |
| Vendor Linking | Email-based | Unclear | ✅ Documented |

---

## Next Steps After Testing

If all tests pass:
1. ✅ Deploy to production
2. ✅ Create vendor accounts for real vendors
3. ✅ Train vendors on using the system
4. ✅ Monitor email delivery
5. ✅ Collect feedback

If tests fail:
1. Check CHANGELOG_VENDOR_FIXES.md for details
2. Check VENDOR_SETUP_GUIDE.md for setup
3. Check backend logs for errors
4. Check browser console for frontend errors

---

**Happy Testing! 🚀**
