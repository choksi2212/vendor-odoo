# VendorBridge — Hackathon Analysis
> Odoo x KSV | Procurement & Vendor Management ERP

---

## 1. What Is This?

A **Procurement & Vendor Management ERP** built on (or inspired by) Odoo architecture. The goal is to digitize the full procurement lifecycle — from vendor registration all the way to invoice dispatch — with role-based access and structured approval workflows.

---

## 2. The Core Problem Being Solved

Organizations waste time on **manual procurement**:
- Vendors managed via spreadsheets or email
- No structured RFQ → Quotation → Approval → PO → Invoice pipeline
- No side-by-side quotation comparison
- No audit trail or activity logs

VendorBridge digitizes and centralizes all of this.

---

## 3. The 8-Step Business Workflow (Critical to Understand)

```
RFQ Created (Procurement Officer)
    ↓
Vendors Invited → Submit Quotations
    ↓
Quotations Compared (Side-by-side)
    ↓
Approval Workflow Triggered (Manager)
    ↓
Approved → Purchase Order Generated (Auto PO#)
    ↓
Invoice Generated from PO
    ↓
Invoice → PDF Download / Print / Email
    ↓
All activity logged → Analytics updated
```

This is the **spine** of the entire application. Every screen must serve one or more of these steps.

---

## 4. User Roles & What They Can Do

| Role | Core Actions |
|---|---|
| **Procurement Officer** | Create RFQs, Compare Quotations, Generate PO, Generate Invoice |
| **Vendor** | Submit Quotations, View RFQ status, View their POs |
| **Manager / Approver** | Approve or Reject procurement requests, Monitor workflows |
| **Admin** | Manage users, Manage vendors, View analytics |

> **Key Insight**: Role-based access is not cosmetic — it determines what screens each user sees and what actions they can perform. The entire app is gated by roles.

---

## 5. Screen-by-Screen Breakdown

### Screen 1 — Login / Signup
- Standard auth (email + password)
- Forgot password flow
- **Role-based redirect after login** (most critical part)
- Session handling + validation

### Screen 2 — Dashboard / Home
- 4 analytics cards: Pending Approvals, Active RFQs, Recent POs, Recent Invoices
- Quick action buttons (Create RFQ, Add Vendor, etc.)
- Role-sensitive: what a Vendor sees ≠ what an Officer sees

### Screen 3 — Vendor Management
- Register vendors with: Name, Category, GST details, Contact info, Status (Active/Inactive)
- Search + filter vendors
- Vendor status tracking

### Screen 4 — RFQ Creation
- Title, product/service details, quantity
- Attachment support
- Deadline picker
- **Assign specific vendors** to receive the RFQ

### Screen 5 — Vendor Quotation Submission
- Vendor-facing screen
- Fill: price, delivery timeline, notes
- Editable until submitted
- Submit action locks the quotation

### Screen 6 — Quotation Comparison
- **Side-by-side comparison** of all quotations for a single RFQ
- Highlight lowest price
- Show delivery timelines
- Vendor rating indicators
- Sort + filter

### Screen 7 — Approval Workflow
- Manager sees pending approvals
- Approve or Reject with remarks
- Visual approval timeline (who approved, when)
- Workflow state transitions (Pending → Approved / Rejected)

### Screen 8 — Purchase Order & Invoice
- Auto-generate PO number upon approval
- Invoice generation from PO
- Tax + total calculations
- **PDF download**, **Print**, **Send via Email**
- Status tracking (Draft → Issued → Paid)

### Screen 9 — Activity Logs & Notifications
- Real-time notifications for: new RFQs, approvals, invoice updates
- Full audit log (who did what, when)
- Activity timeline view

### Screen 10 — Reports & Analytics
- Vendor performance metrics
- Spending summaries
- Monthly procurement trends (charts)
- Exportable reports

---

## 6. Key Technical Requirements

| Concern | Requirement |
|---|---|
| Architecture | Proper ERP module design (reusable, scalable) |
| Auth | Role-based (4 roles), session management |
| Data flow | RFQ → Quotation → PO → Invoice (stateful, linked records) |
| PDF | Invoice must be downloadable as PDF |
| Email | Invoice must be sendable via email |
| UI/UX | Intuitive, clean, procurement-domain appropriate |

---

## 7. What's NOT Explicitly Specified (Assumptions Needed)

- **Database**: Not specified — likely Odoo ORM or PostgreSQL
- **Tech stack**: Not specified — could be Odoo native (Python + XML + QWeb) or custom (React + Node/Django)
- **Email service**: Not specified — SMTP / SendGrid would need integration
- **PDF generation**: Not specified — wkhtmltopdf (Odoo native) or library like ReportLab / jsPDF
- **Vendor invitation mechanism**: Not clear if vendors get email invites or login and see assigned RFQs

---

---

## 10. One-Line Summary

> VendorBridge is a role-gated, workflow-driven procurement ERP where the core value is the structured pipeline from **RFQ → Quotation → Comparison → Approval → PO → Invoice**, with PDF and email delivery as the capstone feature.
