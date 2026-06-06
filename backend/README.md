<div align="center">

<img src="https://img.shields.io/badge/VendorBridge-ERP-0F172A?style=for-the-badge&logo=buffer&logoColor=white" alt="VendorBridge" />

# VendorBridge ERP

### Enterprise-Grade Procurement & Vendor Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![React](https://img.shields.io/badge/React_19-20232A?style=flat-square&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Tests](https://img.shields.io/badge/Tests-232_Passing-4CAF50?style=flat-square&logo=pytest&logoColor=white)]()
[![License](https://img.shields.io/badge/License-Hackathon-blue?style=flat-square)](./LICENSE)
[![Hackathon](https://img.shields.io/badge/Odoo_x_KSV-Hackathon_2026-8B5CF6?style=flat-square&logo=odoo&logoColor=white)](https://github.com)

<br/>

> A full-stack, production-ready ERP solution that digitizes the complete procurement lifecycle —
> from vendor onboarding through invoice dispatch — with real-time notifications, PDF generation,
> email delivery, and comprehensive audit trails.

<br/>

**[Live Demo](#-getting-started)** · **[API Docs](http://localhost:8000/docs)** · **[Backend Branch](https://github.com/choksi2212/vendor-odoo/tree/backend)** · **[Frontend Branch](https://github.com/choksi2212/vendor-odoo/tree/main)**

</div>

---

## Problem Statement

Organizations waste time and resources on manual, fragmented procurement processes:

| Pain Point | Impact |
|---|---|
| Vendors managed via spreadsheets / email | Zero traceability, frequent errors |
| No structured RFQ to Approval to PO pipeline | Delayed procurement cycles |
| No quotation comparison mechanism | Suboptimal vendor selection |
| No audit trail or activity logs | Compliance and accountability gaps |
| Manual invoice generation | Slow payment cycles, no PDF standardization |

**VendorBridge** eliminates all of this through a single, centralized procurement platform with enterprise-grade backend infrastructure.

---

## Core Business Workflow

```
                         VENDORBRIDGE - 8 STEP PROCUREMENT WORKFLOW
                         
  [Procurement Officer]              [Vendor]                  [Manager]
         |                              |                          |
         v                              |                          |
   1. Create RFQ                        |                          |
         |                              |                          |
         v                              |                          |
   2. Invite Vendors -----------------> 3. Submit Quotations       |
                                        |                          |
         <------------------------------+                          |
         |                                                         |
         v                                                         |
   4. Compare Quotations (Side-by-Side Analytics)                  |
         |                                                         |
         v                                                         |
   5. Initiate Approval ------------------------------------> 6. Approve / Reject
                                                                   |
         <---------------------------------------------------------+
         |
         v
   7. Generate Purchase Order (Auto PO-YYYY-XXXX)
         |
         v
   8. Generate Invoice + PDF + Email Dispatch (INV-YYYY-XXXX)
         |
         +---> PDF Generated (ReportLab - Professional Layout)
         +---> Email Sent (Brevo API - With PDF Attachment)
         +---> Activity Logged (Complete Audit Trail)
         +---> Analytics Updated (Real-Time Dashboard)
```

---

## System Architecture

```
+---------------------------+          +----------------------------------+
|      FRONTEND (React)     |   HTTPS  |         BACKEND (FastAPI)        |
|                           | <------> |                                  |
|  - React 19 + TypeScript  |   JWT    |  - FastAPI 0.115.5               |
|  - TanStack Router        |  Bearer  |  - SQLAlchemy 2.0 ORM            |
|  - Tailwind CSS           |          |  - PostgreSQL 18                  |
|  - Radix UI Components    |          |  - Alembic Migrations            |
|  - React Hook Form + Zod  |          |  - Bcrypt Password Hashing       |
|  - Recharts               |          |  - JWT Access + Refresh Tokens   |
|  - Bun Package Manager    |          |  - ReportLab PDF Generation      |
+---------------------------+          |  - Brevo Email API               |
                                       |  - WebSocket Notifications       |
         +                             |  - SlowAPI Rate Limiting         |
         |  WebSocket                  +----------------------------------+
         |  (Real-Time)                              |
         v                                           v
+---------------------------+          +----------------------------------+
|   Browser Notifications   |          |      PostgreSQL Database         |
|   - Instant delivery      |          |                                  |
|   - Approval alerts       |          |  18 Tables:                      |
|   - RFQ updates           |          |  - users, user_sessions          |
|   - Invoice status        |          |  - vendors, vendor_categories    |
+---------------------------+          |  - rfqs, rfq_vendors             |
                                       |  - rfq_attachments               |
                                       |  - quotations                    |
                                       |  - approvals, approval_history   |
                                       |  - purchase_orders, po_line_items|
                                       |  - invoices, invoice_line_items  |
                                       |  - activity_logs, notifications  |
                                       |  - one_time_tokens, otp_codes    |
                                       +----------------------------------+
```

---

## Tech Stack

### Backend

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Framework | FastAPI | 0.115.5 | Async Python API with auto-docs |
| Database | PostgreSQL | 18 | ACID-compliant relational DB |
| ORM | SQLAlchemy | 2.0.36 | Type-safe database operations |
| Migrations | Alembic | 1.14.0 | Schema version control |
| Auth | python-jose + bcrypt | 3.3.0 | JWT tokens + password hashing |
| PDF | ReportLab | 4.0.7 | Professional invoice generation |
| Email | Brevo HTTP API | - | Transactional email delivery |
| WebSocket | FastAPI native | - | Real-time notifications |
| Rate Limiting | SlowAPI | 0.1.9 | DDoS protection |
| Testing | Pytest | 8.3.4 | 232 automated tests |
| Validation | Pydantic | 2.9.2 | Request/response validation |

### Frontend

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Framework | React | 19.2.0 | Component-based UI |
| Routing | TanStack Router | 1.168.25 | Type-safe file-based routing |
| Styling | Tailwind CSS | 4.2.1 | Utility-first CSS |
| UI Library | Radix UI | Latest | Accessible primitives |
| Forms | React Hook Form + Zod | 7.71 / 3.24 | Validation |
| Charts | Recharts | 2.15.4 | Data visualization |
| Build | Vite | 7.3.1 | Fast HMR and builds |
| Package Manager | Bun | 1.0+ | Fast dependency management |

---

## Key Features

### Authentication & Security
- JWT access tokens (15-min expiry) + refresh token rotation (7-day)
- Bcrypt password hashing with 12 rounds
- Account locking after 5 failed attempts (30-min lockout)
- Two-factor authentication via email OTP
- Email verification for new accounts
- Password reset with one-time tokens
- Rate limiting on sensitive endpoints
- Role-based access control (4 roles)

### Vendor Management
- Complete CRUD with GST number validation (Indian format)
- Vendor categorization system
- Active/Inactive status management
- Search, filter, and pagination
- Performance metrics per vendor

### RFQ Management
- Create, update, delete RFQs
- Multi-vendor assignment
- Status workflow: Draft -> Open -> Closed
- File attachment support
- Deadline tracking

### Quotation System
- Vendor quotation submission with auto-total calculation
- Draft -> Submit locking mechanism
- Side-by-side comparison with analytics
- Lowest price and fastest delivery highlighting
- Min/max/average calculations

### Approval Workflow
- Multi-step approval chain
- Separation of duties (self-approval blocked)
- Approve/reject with remarks
- Complete history timeline
- Email notifications to stakeholders

### Purchase Order Generation
- Auto-generated from approved quotations
- Sequential numbering: PO-YYYY-XXXX (resets per year)
- Line items from RFQ product data
- Automatic 18% GST calculation
- Status lifecycle: Issued -> Paid / Cancelled

### Invoice & PDF System
- Invoice creation from Purchase Orders
- Sequential numbering: INV-YYYY-XXXX (resets per year)
- Professional PDF generation (ReportLab):
  - Company branding header
  - Bill-to section with vendor details
  - Line items table with formatting
  - Tax breakdown and grand total
  - Payment terms and footer
- Email delivery with PDF attachment (Brevo API)
- Status workflow: Draft -> Issued -> Paid

### Analytics & Reporting
- Real-time dashboard (pending approvals, active RFQs, spend)
- Vendor performance metrics (submission rate, win rate, order value)
- Monthly trends (6-month history)
- Spending breakdown by vendor with percentages
- Complete activity audit trail

### Real-Time Notifications
- WebSocket-based instant delivery
- JWT-authenticated connections
- Multi-tab support (multiple connections per user)
- Notification types: INFO, WARNING, ERROR, SUCCESS
- Mark read / mark all read

---

## Database Design

### Entity Relationship Overview (18 Tables)

```
users ──────────── user_sessions
  |                one_time_tokens
  |                otp_codes
  |
  +── vendors ──── vendor_categories
  |     |
  |     +── rfq_vendors ── rfqs ── rfq_attachments
  |                          |
  |                          +── quotations
  |                                  |
  |                          +── approvals ── approval_history
  |                                  |
  |                          +── purchase_orders ── po_line_items
  |                                  |
  |                          +── invoices ── invoice_line_items
  |
  +── activity_logs
  +── notifications
```

### Key Design Decisions
- **UUID primary keys** for all tables (distributed-system ready)
- **Proper indexing** on all foreign keys and frequently queried columns
- **Soft deletes** for vendors (status change, not row deletion)
- **JSONB** for activity log details (flexible audit data)
- **Cascading deletes** where appropriate (RFQ -> quotations -> approvals)
- **Unique constraints** on GST numbers, PO numbers, invoice numbers
- **Check constraints** on numeric fields (quantity > 0, price >= 0)

---

## API Documentation

### Complete Endpoint Reference (50+ Endpoints)

| Module | Endpoints | Auth Required |
|---|---|---|
| Authentication | 9 endpoints | Mixed |
| Users | 3 endpoints | Yes |
| Vendors | 7 endpoints | Yes (Role-based) |
| RFQs | 8 endpoints | Yes (Role-based) |
| Quotations | 6 endpoints | Yes (Role-based) |
| Approvals | 5 endpoints | Yes (Role-based) |
| Purchase Orders | 4 endpoints | Yes (Role-based) |
| Invoices | 6 endpoints | Yes (Role-based) |
| Analytics | 4 endpoints | Yes (Role-based) |
| Notifications | 3 endpoints | Yes |
| Activity Logs | 1 endpoint | Yes (Admin only) |
| WebSocket | 1 endpoint | Yes (JWT query param) |

### Interactive API Documentation

Once the backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Role-Based Access Matrix

| Feature | Procurement Officer | Vendor | Manager | Admin |
|---|:---:|:---:|:---:|:---:|
| Dashboard & Analytics | Full | Limited | Full | Full |
| Vendor Management | Create/Edit | View Only | View Only | Full |
| RFQ Management | Full CRUD | View Assigned | View Only | Full |
| Submit Quotations | No | Yes | No | No |
| Compare Quotations | Yes | No | Yes | Yes |
| Request Approval | Yes | No | No | Yes |
| Approve/Reject | No | No | Yes | Yes |
| Purchase Orders | Create/View | No | View | Full |
| Invoices & PDF | Full | No | View | Full |
| Activity Logs | View Own | View Own | No | Full Audit |
| Admin Settings | No | No | No | Full |

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (we use 18)
- Node.js 18+ or Bun 1.0+
- Git

### Backend Setup

```bash
# Clone repository
git clone https://github.com/choksi2212/vendor-odoo.git
cd vendor-odoo
git checkout backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE vendorbridge;"

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL password and Brevo API key

# Create tables
python -c "from app.db.base import Base; from app.db.session import engine; from app.models import *; Base.metadata.create_all(bind=engine)"

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
# Switch to main branch
git checkout main

# Install dependencies
bun install

# Start development server
bun run dev
```

### Running Tests

```bash
# Backend (232 tests)
cd backend
.venv\Scripts\activate
pytest tests/ -v

# Expected output: 232 passed
```

---

## Testing

### Test Coverage Summary

| Module | Tests | Coverage |
|---|---|---|
| Authentication | 43 | Signup, login, token refresh, 2FA, password reset, account locking |
| Vendor Management | 41 | CRUD, GST validation, search, filter, pagination, RBAC |
| RFQ Management | 34 | CRUD, lifecycle, vendor assignment, publish, close |
| Quotation System | 22 | Create, submit, update, comparison analytics |
| Approval Workflow | 20 | Create, approve, reject, history, separation of duties |
| Purchase Orders | 17 | Generation, numbering, tax calculation, status transitions |
| Invoice & PDF | 16 | Creation, PDF generation, status workflow, mark paid |
| Analytics | 23 | Dashboard, vendor performance, trends, notifications, logs |
| WebSocket | 16 | Connection, auth, ping/pong, notification service |
| **TOTAL** | **232** | **All passing** |

### Real-World Workflow Verification

The complete procurement workflow has been verified end-to-end against a live PostgreSQL database:

```
Step  1: User Registration        -> 3 users created (officer, manager, admin)
Step  2: Login with JWT           -> Access + refresh tokens issued
Step  3: Create Vendor            -> Stored in PostgreSQL with GST validation
Step  4: Create RFQ               -> Draft status, product specifications stored
Step  5: Assign Vendor + Publish  -> RFQ status: draft -> open
Step  6: Submit Quotation         -> Rs.92,500/unit x 80 = Rs.74,00,000
Step  7: Request Approval         -> Pending approval created
Step  8: Manager Approves         -> Status: approved, remarks stored
Step  9: Generate PO              -> PO-2026-0001, Rs.87,32,000 (incl. 18% GST)
Step 10: Generate Invoice         -> INV-2026-0001, line items copied
Step 11: Download PDF             -> 3,120 bytes, valid %PDF header
Step 12: Issue + Mark Paid        -> Cascades to PO status
Step 13: Dashboard Analytics      -> Real aggregated data displayed
Step 14: Database Verification    -> All data persisted in PostgreSQL
```

---

## Design System

| Token | Value | Usage |
|---|---|---|
| Primary Dark | `#0F172A` | Sidebar, headings |
| Action Blue | `#2563EB` | Buttons, links, active states |
| Success Green | `#16A34A` | Active / Approved badges |
| Warning Yellow | `#CA8A04` | Pending badges |
| Danger Red | `#DC2626` | Rejected badges |
| Draft Blue | `#2563EB` | Draft status badges |
| Font - Headings | `Sora` | Page titles, section headers |
| Font - Body | `DM Sans` | All body text, tables, forms |

---

## Deployment

### Backend (Railway)

```bash
# Procfile handles deployment
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Railway auto-detects via `Procfile`, `nixpacks.toml`, and `railway.json`.

### Frontend (Vercel/Netlify)

```bash
bun run build    # Creates dist/ folder
# Deploy dist/ to Vercel or Netlify
```

### Environment Variables (Production)

```env
DATABASE_URL=postgresql://user:pass@host:5432/vendorbridge
SECRET_KEY=<64-char-hex-string>
BREVO_API_KEY=<your-brevo-key>
BREVO_SENDER_EMAIL=<verified-email>
ALLOWED_ORIGINS=["https://your-frontend-domain.com"]
```

---

## Git Workflow

```
main branch     -> Frontend (React + TailwindCSS)
backend branch  -> Backend (FastAPI + PostgreSQL)
```

### Commit History (Backend)

```
Phase  1: Project structure and dependencies
Phase  2: Database models (18 tables)
Phase  3: Authentication system (JWT, 2FA, bcrypt)
Phase  4: Vendor management (CRUD, GST validation)
Phase  5: RFQ management (lifecycle, vendor assignment)
Phase  6: Quotation system (comparison analytics)
Phase  7: Approval workflow (history, separation of duties)
Phase  8: Purchase order generation (auto-numbering, tax)
Phase  9: Invoice & PDF generation (ReportLab)
Phase 10: Analytics & reporting (dashboard, trends)
Phase 11: WebSocket notifications (real-time)
Phase 12: Deployment configuration
```

---

## Hackathon Evaluation Criteria Addressed

| Criteria | How We Address It |
|---|---|
| **Database Design** | 18 normalized tables with proper FK, indexes, constraints, UUID PKs |
| **Coding Standards** | Clean Python (PEP8), TypeScript strict, modular architecture |
| **Logic & Modularity** | Service layer pattern, single responsibility, DRY |
| **Frontend Design** | Enterprise ERP UI, consistent design system, responsive |
| **Performance** | Connection pooling, indexed queries, rate limiting, code splitting |
| **Scalability** | Stateless JWT auth, PostgreSQL, async FastAPI, WebSocket |
| **Security** | Bcrypt, JWT rotation, account locking, input validation, CORS |
| **Usability** | Intuitive navigation, role-based menus, real-time feedback |
| **Real-Time Data** | Live PostgreSQL queries, WebSocket notifications, no static JSON |
| **Input Validation** | Pydantic schemas (backend) + Zod schemas (frontend) |
| **Git Usage** | Meaningful commits, branch strategy, clean history |
| **Attention to Detail** | GST format validation, sequential numbering, tax calculations |

---

## Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/hemathens">
        <img src="https://github.com/hemathens.png" width="80px" style="border-radius:50%" alt="hemathens"/><br/>
        <sub><b>Hem Patel</b></sub>
      </a><br/>
      <sub>Frontend Architecture | UI/UX Design | React Components</sub>
    </td>
    <td align="center">
      <a href="https://github.com/choksi2212">
        <img src="https://github.com/choksi2212.png" width="80px" style="border-radius:50%" alt="choksi2212"/><br/>
        <sub><b>Manas Choksi</b></sub>
      </a><br/>
      <sub>Backend Architecture | Database Design | API Development | DevOps</sub>
    </td>
  </tr>
</table>

---

## License

This project was developed for the **Odoo x KSV Hackathon 2026**.
All rights reserved by the contributors.

---

<div align="center">

**Built with precision for the Odoo x KSV Hackathon**

[![hemathens](https://img.shields.io/badge/GitHub-hemathens-181717?style=flat-square&logo=github)](https://github.com/hemathens)
[![choksi2212](https://img.shields.io/badge/GitHub-choksi2212-181717?style=flat-square&logo=github)](https://github.com/choksi2212)

*Enterprise Procurement Management — Digitized, Streamlined, Secured.*

</div>
