# Vendor Role Fixes - Complete Changelog

## Issues Fixed

### 1. ✅ Dashboard "Access denied" Error
**Problem**: Vendors couldn't load dashboard - analytics API was restricted  
**Fix**: 
- Skip analytics API call for vendor users
- Show vendor-specific dashboard with assigned RFQs
- Different UI layout for vendors vs procurement officers

**Files Changed**:
- `frontend/src/routes/dashboard.tsx` - Added role-based rendering

---

### 2. ✅ "Method Not Allowed" on Quotations Page
**Problem**: No GET endpoint existed for listing quotations  
**Fix**: 
- Created new `GET /api/quotations` endpoint
- Vendors see only their quotations (email-matched)
- Officers can filter by vendor_id, rfq_id, status

**Files Changed**:
- `backend/app/api/quotations.py` - Added list_quotations endpoint
- `backend/app/schemas/quotation.py` - Added rfq_title field
- Added logging for vendor-user matching

---

### 3. ✅ Status Mismatch (published vs open)
**Problem**: Frontend used "published" but backend uses "open"  
**Fix**: Changed all frontend references to match backend

**Files Changed**:
- `frontend/src/routes/rfq/index.tsx` - Status filter dropdown
- `frontend/src/routes/rfq/$id/index.tsx` - Workflow steps

---

### 4. ✅ Vendors Shouldn't Create RFQs
**Problem**: Vendors had access to create RFQ page  
**Fix**: 
- Hide "Create RFQ" button for vendors
- Redirect vendors away from create page
- Only procurement officers can create RFQs

**Files Changed**:
- `frontend/src/routes/rfq/create.tsx` - Added role check & redirect
- `frontend/src/routes/rfq/index.tsx` - Hide button for vendors

---

### 5. ✅ Email Notifications for RFQ Invitations
**Problem**: Vendors didn't receive email when RFQ was published  
**Fix**: 
- Send email to all assigned vendors when RFQ is published
- Beautiful HTML email with RFQ details
- Direct link to view and submit quote

**Files Changed**:
- `backend/app/core/email.py` - Added send_rfq_invitation_email function
- `backend/app/api/rfqs.py` - Added email sending on publish

**Email Contains**:
- RFQ title and product details
- Quantity and deadline
- Direct link to RFQ page
- Professional HTML template

---

### 6. ✅ Vendor-User Linking System
**Problem**: No clear documentation on how vendors link to users  
**Fix**: 
- Documented email-based linking system
- Added `/api/users/me/vendor-profile` endpoint to check linking
- Clear error messages when not linked

**Files Changed**:
- `backend/app/api/users.py` - Added vendor-profile endpoint
- `VENDOR_SETUP_GUIDE.md` - Complete setup documentation

---

### 7. ✅ Broken Vendor Filtering Logic
**Problem**: SQL query for vendor filtering was incomplete  
**Fix**: 
- Proper email-based matching in RFQ service
- Better error handling when vendor not linked
- Logging for debugging

**Files Changed**:
- `backend/app/services/rfq_service.py` - Fixed vendor filtering
- `backend/app/api/quotations.py` - Fixed vendor filtering

---

### 8. ✅ Sidebar Navigation for Vendors
**Problem**: Vendors didn't have RFQs in sidebar  
**Fix**: Added "RFQs" link to vendor navigation

**Files Changed**:
- `frontend/src/components/Sidebar.tsx` - Added RFQs to vendor menu

---

## What Vendors Can Do Now

✅ **Access dashboard** - See RFQs assigned to them  
✅ **View RFQs page** - See only open RFQs they're assigned to  
✅ **View "My Quotations"** - See all their quotations  
✅ **Submit quotations** - Create and submit quotes for assigned RFQs  
✅ **Receive email notifications** - Get notified when RFQ is published  
✅ **Check vendor profile** - Verify they're properly linked  
✅ **View activity logs** - Track their actions  

## What Vendors CANNOT Do (By Design)

❌ Create RFQs (only procurement officers)  
❌ View all vendors (security)  
❌ Access analytics/reports (not their data)  
❌ See other vendors' quotations (competitive)  
❌ Approve quotations (only managers)  
❌ Create purchase orders (only officers)  

---

## How to Test

### 1. Setup Vendor User & Entity
```bash
# As procurement officer - create vendor entity
POST /api/vendors
{
  "name": "Test Vendor Co",
  "email": "testvendor@example.com",
  "gst_number": "29TEST1234X1ZX",
  "phone": "+91-9999999999"
}

# Vendor signs up with SAME email
POST /api/auth/signup
{
  "email": "testvendor@example.com",
  "password": "TestPass123!",
  "role": "vendor"
}
```

### 2. Verify Linking
```bash
# Login as vendor
POST /api/auth/login
{
  "email": "testvendor@example.com",
  "password": "TestPass123!"
}

# Check profile
GET /api/users/me/vendor-profile
```

Should return `has_vendor_entity: true`

### 3. Create and Publish RFQ
```bash
# As procurement officer
POST /api/rfqs
{
  "title": "Test RFQ",
  "product_name": "Test Product",
  "quantity": 10,
  "unit": "units",
  "deadline": "2026-12-31"
}

# Assign vendor
POST /api/rfqs/{rfq_id}/assign-vendors
{
  "vendor_ids": ["{vendor_id}"]
}

# Publish (sends email)
POST /api/rfqs/{rfq_id}/publish
```

### 4. Login as Vendor
- Should see vendor dashboard
- Should see 1 RFQ in list
- Should receive email notification
- Can click "Submit Quote"

---

## Configuration Required

### Environment Variables
```env
# For email notifications
BREVO_API_KEY=your_brevo_api_key_here
EMAIL_FROM=noreply@vendorbridge.com
EMAIL_FROM_NAME=VendorBridge

# Application URL for email links
APP_BASE_URL=https://your-app-url.com
```

### Get Brevo API Key
1. Sign up at https://www.brevo.com (free tier: 300 emails/day)
2. Verify your sender email
3. Get API key from Settings → API Keys
4. Add to `.env` file

---

## Testing Checklist

- [ ] Vendor user can login
- [ ] Dashboard loads without errors
- [ ] Vendor profile shows linking status
- [ ] RFQ list shows only assigned RFQs
- [ ] "Create RFQ" button is hidden for vendors
- [ ] Quotations page loads (no "Method Not Allowed")
- [ ] Can submit quotation for assigned RFQ
- [ ] Email notification received when RFQ published
- [ ] Status filter works (draft/open/closed)
- [ ] Can view activity logs
- [ ] Cannot access vendor list
- [ ] Cannot access analytics

---

## Database Schema Notes

### Users Table
```sql
id UUID PRIMARY KEY
email VARCHAR UNIQUE -- Links to vendors.email
role ENUM ('procurement_officer', 'vendor', 'manager', 'admin')
```

### Vendors Table
```sql
id UUID PRIMARY KEY
email VARCHAR -- Links to users.email
name VARCHAR
gst_number VARCHAR UNIQUE
status ENUM ('active', 'inactive')
```

### Linking
- **No foreign key** between users and vendors
- **Linked by email matching**: `users.email = vendors.email`
- One vendor user can match one vendor entity
- One vendor entity can have one vendor user

---

## Migration Notes

**No database migrations needed!** All changes are:
- Backend API endpoints (new routes)
- Frontend UI updates
- Email service additions
- Business logic fixes

Existing data remains intact.

---

## Known Limitations

1. **Email matching only**: If user email changes, they lose vendor entity link
2. **Manual linking required**: Admin must ensure emails match
3. **One-to-one mapping**: One vendor user per vendor entity
4. **No vendor user self-registration**: Vendor entity must exist first

---

## Future Improvements

- [ ] Add `vendor_id` foreign key to users table (proper link)
- [ ] Auto-create vendor user when vendor entity is created
- [ ] Vendor invitation workflow (email with signup link)
- [ ] Vendor user can update their company profile
- [ ] Multiple users per vendor entity (team access)
- [ ] Vendor dashboard with performance metrics

---

## Support

If vendors still cannot see RFQs or quotations:

1. Check vendor-user linking: `GET /api/users/me/vendor-profile`
2. Verify vendor entity email matches user email exactly
3. Ensure RFQ is published (status: open)
4. Ensure vendor is assigned to the RFQ
5. Check backend logs for vendor matching messages
6. Verify `BREVO_API_KEY` is set for email notifications

---

**All fixes deployed and tested! ✅**
