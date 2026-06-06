<div align="center">

<img src="https://img.shields.io/badge/VendorBridge-ERP-0F172A?style=for-the-badge&logo=buffer&logoColor=white" alt="VendorBridge" />

# VendorBridge

### Enterprise-Grade Procurement & Vendor Management ERP System

<br/>

## [🚀 LIVE DEMO → https://vendor-odoo.vercel.app](https://vendor-odoo.vercel.app)

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![React](https://img.shields.io/badge/React_19-20232A?style=flat-square&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS_4-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Tests](https://img.shields.io/badge/Tests-232_Passing-4CAF50?style=flat-square&logo=pytest&logoColor=white)]()
[![Hackathon](https://img.shields.io/badge/Odoo_x_KSV-Hackathon_2026-8B5CF6?style=flat-square&logo=odoo&logoColor=white)](https://github.com)

<br/>

> A full-stack, production-ready ERP system that digitizes the complete procurement lifecycle from vendor onboarding to invoice dispatch, with real-time notifications, professional PDF generation, email delivery, and comprehensive audit trails.

<br/>

| | Link |
|---|---|
| **Live Application** | **https://vendor-odoo.vercel.app** |
| **Backend API** | https://vendor-odoo-production.up.railway.app |
| **API Documentation** | https://vendor-odoo-production.up.railway.app/docs |

</div>

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Complete Procurement Workflow](#complete-procurement-workflow)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Design](#database-design)
- [API Endpoints](#api-endpoints)
- [Role-Based Access Control](#role-based-access-control)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [Security Implementation](#security-implementation)
- [Deployment](#deployment)
- [Contributors](#contributors)

---

## Problem Statement

Organizations struggle with fragmented, manual procurement processes that lead to:

| Pain Point | Business Impact |
|---|---|
| Vendors managed in spreadsheets/email | Zero traceability, duplicate data, frequent errors |
| No structured RFQ-to-PO pipeline | 2-3 week delays in procurement cycles |
| No quotation comparison mechanism | 15-20% overspend due to suboptimal vendor selection |
| No approval workflow | Unauthorized purchases, compliance violations |
| Manual invoice generation | Slow payment cycles, no audit trail |
| No analytics or reporting | Inability to track spend patterns or vendor performance |

**VendorBridge solves all of these** through a centralized, role-gated procurement platform with enterprise-grade security and real-time data.

---

## Solution Overview

VendorBridge implements a complete **8-step procurement lifecycle** as a full-stack web application:

```
    VENDOR ONBOARDING          SOURCING              EVALUATION
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  Register Vendor  │  │   Create RFQ     │  │ Compare Quotes   │
   │  Validate GST     │──│   Assign Vendors │──│ Side-by-Side     │
   │  Categorize       │  │   Set Deadline   │  │ Analytics        │
   └──────────────────┘  └──────────────────┘  └──────────────────┘
                                                         │
         PAYMENT               FULFILLMENT         GOVERNANCE
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  Generate Invoice │  │  Issue PO        │  │  Manager Approves│
   │  PDF + Email      │──│  Auto Numbering  │──│  Audit Trail     │
   │  Mark Paid        │  │  Tax Calculation │  │  Notifications   │
   └──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## Complete Procurement Workflow

```
  STEP 1                STEP 2               STEP 3               STEP 4
  ┌─────┐              ┌─────┐              ┌─────┐              ┌─────┐
  │ RFQ │    Publish    │     │   Submit     │     │   Compare    │     │
  │ Cre-│─────────────→ │ RFQ │────────────→ │Quot-│────────────→ │Eval-│
  │ ate │   + Assign    │ Open│   Quotation  │atio-│   Side by    │uate │
  └─────┘   Vendors     └─────┘              │ ns  │   Side       └─────┘
  Officer               Officer              Vendor               Officer
                                                                     │
  STEP 8                STEP 7               STEP 6               STEP 5
  ┌─────┐              ┌─────┐              ┌─────┐              ┌─────┐
  │ Pay │    Mark       │ Inv-│   Generate   │ PO  │    Auto      │Appr-│
  │ men-│←──────────────│oice │←─────────────│Gene-│←─────────────│oval │
  │ t   │    Paid       │ PDF │   Invoice    │rate │    on OK     │     │
  └─────┘              └─────┘              └─────┘              └─────┘
  Officer              Officer              System               Manager
```

**Detailed Flow:**

1. **Procurement Officer** creates an RFQ specifying product, quantity, deadline
2. **System** assigns selected vendors and publishes the RFQ (sends email invitations)
3. **Vendors** submit competitive quotations with pricing and delivery timelines
4. **Officer** uses side-by-side comparison with analytics (lowest price, fastest delivery highlighted)
5. **Officer** selects best quotation and sends to **Manager** for approval
6. **Manager** reviews and approves (or rejects with remarks)
7. **System** auto-generates Purchase Order (PO-YYYY-XXXX) with 18% GST calculation
8. **Officer** generates Invoice (INV-YYYY-XXXX), downloads PDF, emails to vendor, marks paid

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT                                      │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  React 19 + TypeScript + TailwindCSS + TanStack Router         │     │
│  │  - Role-based navigation and UI rendering                      │     │
│  │  - Real-time WebSocket notifications                           │     │
│  │  - JWT token management with auto-refresh                      │     │
│  └────────────────────────────────┬───────────────────────────────┘     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │ HTTPS + JWT Bearer
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND API                                    │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  FastAPI 0.115.5 (Python 3.11)                                 │     │
│  │                                                                │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │     │
│  │  │   API    │  │ Service  │  │  Models  │  │ Schemas  │     │     │
│  │  │  Layer   │→ │  Layer   │→ │  (ORM)   │→ │(Pydantic)│     │     │
│  │  │ (Routes) │  │ (Logic)  │  │(SQLAlch.)│  │(Validat.)│     │     │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │     │
│  │                                                                │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │     │
│  │  │   JWT    │  │  Bcrypt  │  │ SlowAPI  │  │WebSocket │     │     │
│  │  │   Auth   │  │ Hashing  │  │Rate Limit│  │  Notify  │     │     │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │     │
│  └────────────────────────────────┬───────────────────────────────┘     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │ SQL (SQLAlchemy ORM)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL 18                                     │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  18 Tables | Indexed | Foreign Keys | Constraints | ACID       │     │
│  └────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────┐    ┌──────────┐    ┌──────────┐
            │  Brevo   │    │ReportLab │    │   File   │
            │Email API │    │   PDF    │    │ Storage  │
            └──────────┘    └──────────┘    └──────────┘
```

---

## Tech Stack

### Backend

| Component | Technology | Purpose |
|---|---|---|
| Framework | FastAPI 0.115.5 | High-performance async Python API |
| Database | PostgreSQL 18 | ACID-compliant relational database |
| ORM | SQLAlchemy 2.0.36 | Type-safe database operations |
| Migrations | Alembic 1.14.0 | Schema version control |
| Auth | python-jose + bcrypt | JWT tokens + password hashing (12 rounds) |
| PDF | ReportLab 4.0.7 | Professional invoice PDF generation |
| Email | Brevo HTTP API | Transactional email (verification, OTP, invoices) |
| WebSocket | FastAPI native | Real-time notification delivery |
| Rate Limiting | SlowAPI 0.1.9 | Brute-force and DDoS protection |
| Validation | Pydantic 2.9.2 | Request/response schema validation |
| Testing | Pytest 8.3.4 | 232 automated tests (100% pass) |

### Frontend

| Component | Technology | Purpose |
|---|---|---|
| Framework | React 19.2.0 | Component-based UI |
| Language | TypeScript 5.8.3 | Type safety |
| Routing | TanStack Router 1.168.25 | Type-safe file-based routing |
| Styling | Tailwind CSS 4.2.1 | Utility-first responsive design |
| UI Primitives | Radix UI | Accessible, unstyled components |
| Forms | React Hook Form + Zod | Validation with type inference |
| Charts | Recharts 2.15.4 | Data visualization |
| Build | Vite 7.3.1 | Fast HMR and production builds |

---

## Project Structure

```
vendorbridge/
├── backend/                          # FastAPI + PostgreSQL Backend
│   ├── app/
│   │   ├── api/                      # API route handlers
│   │   │   ├── auth.py              # Authentication (signup, login, 2FA, reset)
│   │   │   ├── users.py             # User profile, 2FA toggle
│   │   │   ├── vendors.py           # Vendor CRUD + categories
│   │   │   ├── rfqs.py              # RFQ lifecycle management
│   │   │   ├── quotations.py        # Quotation submit + comparison
│   │   │   ├── approvals.py         # Approval workflow
│   │   │   ├── purchase_orders.py   # PO generation + status
│   │   │   ├── invoices.py          # Invoice + PDF + email
│   │   │   ├── analytics.py         # Dashboard + reports
│   │   │   ├── notifications.py     # User notifications
│   │   │   ├── activity_logs.py     # Audit trail
│   │   │   └── websocket.py         # Real-time WebSocket
│   │   ├── core/                     # Shared utilities
│   │   │   ├── config.py            # Environment configuration
│   │   │   ├── security.py          # JWT, bcrypt, rate limiter
│   │   │   ├── dependencies.py      # Auth guards, role checks
│   │   │   ├── email.py             # Brevo email templates
│   │   │   └── websocket.py         # Connection manager
│   │   ├── db/                       # Database layer
│   │   │   ├── base.py              # SQLAlchemy Base + GUID type
│   │   │   └── session.py           # Engine + session factory
│   │   ├── models/                   # ORM models (18 tables)
│   │   ├── schemas/                  # Pydantic request/response models
│   │   ├── services/                 # Business logic layer
│   │   │   ├── auth_service.py      # Auth logic (signup, login, 2FA)
│   │   │   ├── vendor_service.py    # Vendor CRUD logic
│   │   │   ├── rfq_service.py       # RFQ lifecycle logic
│   │   │   ├── quotation_service.py # Quotation + comparison
│   │   │   ├── approval_service.py  # Approval workflow logic
│   │   │   ├── purchase_order_service.py # PO generation
│   │   │   ├── invoice_service.py   # Invoice management
│   │   │   ├── pdf_service.py       # PDF generation (ReportLab)
│   │   │   ├── analytics_service.py # Dashboard calculations
│   │   │   ├── notification_service.py # Notification creation
│   │   │   └── activity_logger.py   # Audit trail logging
│   │   └── main.py                   # Application entry point
│   ├── tests/                        # 232 automated tests
│   ├── alembic/                      # Database migrations
│   ├── requirements.txt              # Production dependencies
│   └── Dockerfile                    # Container deployment
│
├── frontend/                         # React 19 + TypeScript Frontend
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   │   ├── Layout.tsx           # Main app layout with sidebar
│   │   │   ├── Sidebar.tsx          # Role-based navigation
│   │   │   ├── Table.tsx            # Enterprise data table
│   │   │   ├── Badge.tsx            # Status badges
│   │   │   ├── Button.tsx           # Button variants
│   │   │   ├── StatCard.tsx         # Dashboard metric cards
│   │   │   └── ui/                  # Radix UI primitives (30+)
│   │   ├── routes/                   # File-based routing (23 pages)
│   │   │   ├── login.tsx            # JWT login
│   │   │   ├── signup.tsx           # Registration with role
│   │   │   ├── verify-email.tsx     # Email verification
│   │   │   ├── dashboard.tsx        # Analytics dashboard
│   │   │   ├── vendors/             # Vendor management (list/add/view/edit)
│   │   │   ├── rfq/                 # RFQ management (list/create/detail/compare)
│   │   │   ├── quotations/          # Quotation submission
│   │   │   ├── approvals.tsx        # Approval workflow
│   │   │   ├── purchase-orders/     # PO list and detail
│   │   │   ├── invoices/            # Invoice list/detail/create
│   │   │   ├── activity-logs.tsx    # Audit trail viewer
│   │   │   ├── reports.tsx          # Analytics and charts
│   │   │   └── settings.tsx         # Admin panel
│   │   ├── context/AuthContext.tsx   # JWT auth state management
│   │   ├── lib/api/                  # API client + endpoint functions
│   │   └── data/mockData.ts          # Fallback mock data
│   ├── package.json
│   └── vite.config.ts
│
└── README.md                         # This file
```

---

## Database Design

### 18 Tables with Full Relational Integrity

```
┌─────────────────────────────────────────────────────────────────┐
│                        CORE ENTITIES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  users ◄──── user_sessions (refresh tokens)                      │
│    │    ◄──── one_time_tokens (email verification, password reset)│
│    │    ◄──── otp_codes (2FA codes)                              │
│    │                                                              │
│    ├──► vendors ◄──── vendor_categories                          │
│    │       │                                                      │
│    │       ├──► rfq_vendors (junction) ──► rfqs                  │
│    │       │                                 │                    │
│    │       │                                 ├──► rfq_attachments │
│    │       │                                 │                    │
│    │       └──► quotations ◄─────────────────┘                   │
│    │               │                                              │
│    │               └──► approvals ──► approval_history            │
│    │                       │                                      │
│    │                       └──► purchase_orders ──► po_line_items │
│    │                               │                              │
│    │                               └──► invoices ──► invoice_line_items│
│    │                                                              │
│    ├──► activity_logs (complete audit trail)                      │
│    └──► notifications (real-time alerts)                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **UUID primary keys** on all tables (distributed-system ready)
- **Indexed foreign keys** for fast JOINs
- **Unique constraints** on GST numbers, PO numbers (PO-YYYY-XXXX), invoice numbers (INV-YYYY-XXXX)
- **Check constraints** on quantities (>0), prices (>=0), ratings (0-5)
- **Cascading deletes** where appropriate (RFQ deletion cascades to quotations)
- **Soft deletes** for vendors (status change, not row deletion)
- **JSON column** for activity log details (flexible audit metadata)
- **Sequential numbering** per year for POs and invoices (resets annually)

---

## API Endpoints

### 57 Endpoints Across 12 Modules

| Module | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | POST | `/api/auth/signup` | Register with role selection |
| | POST | `/api/auth/login` | JWT login (returns access + refresh) |
| | POST | `/api/auth/verify-email` | Email verification |
| | POST | `/api/auth/verify-otp` | 2FA OTP verification |
| | POST | `/api/auth/refresh` | Token rotation |
| | POST | `/api/auth/logout` | Revoke refresh token |
| | POST | `/api/auth/forgot-password` | Request password reset |
| | POST | `/api/auth/reset-password` | Reset with token |
| | POST | `/api/auth/resend-verification` | Resend verification email |
| **Users** | GET | `/api/users/me` | Current user profile |
| | POST | `/api/users/2fa/enable` | Enable 2FA |
| | POST | `/api/users/2fa/disable` | Disable 2FA |
| **Vendors** | GET | `/api/vendors` | List (paginated, searchable) |
| | POST | `/api/vendors` | Create vendor |
| | GET | `/api/vendors/{id}` | Get vendor detail |
| | PUT | `/api/vendors/{id}` | Update vendor |
| | DELETE | `/api/vendors/{id}` | Deactivate vendor |
| | GET | `/api/vendors/categories` | List categories |
| | POST | `/api/vendors/categories` | Create category |
| **RFQs** | GET | `/api/rfqs` | List RFQs |
| | POST | `/api/rfqs` | Create RFQ |
| | GET | `/api/rfqs/{id}` | RFQ detail with vendors |
| | PUT | `/api/rfqs/{id}` | Update (draft only) |
| | DELETE | `/api/rfqs/{id}` | Delete (draft only) |
| | POST | `/api/rfqs/{id}/assign-vendors` | Assign vendors |
| | POST | `/api/rfqs/{id}/publish` | Publish (draft->open) |
| | POST | `/api/rfqs/{id}/close` | Close (open->closed) |
| **Quotations** | POST | `/api/quotations` | Create quotation |
| | GET | `/api/quotations/{id}` | Get quotation |
| | PUT | `/api/quotations/{id}` | Update (draft only) |
| | POST | `/api/quotations/{id}/submit` | Submit (locks) |
| | GET | `/api/quotations/rfq/{id}/list` | List per RFQ |
| | GET | `/api/quotations/rfq/{id}/compare` | Comparison analytics |
| **Approvals** | GET | `/api/approvals` | List approvals |
| | POST | `/api/approvals` | Create request |
| | GET | `/api/approvals/{id}` | Detail with history |
| | POST | `/api/approvals/{id}/approve` | Approve |
| | POST | `/api/approvals/{id}/reject` | Reject with remarks |
| **Purchase Orders** | GET | `/api/purchase-orders` | List POs |
| | POST | `/api/purchase-orders` | Generate from approval |
| | GET | `/api/purchase-orders/{id}` | PO detail |
| | PUT | `/api/purchase-orders/{id}/status` | Update status |
| **Invoices** | GET | `/api/invoices` | List invoices |
| | POST | `/api/invoices` | Create from PO |
| | GET | `/api/invoices/{id}` | Invoice detail |
| | GET | `/api/invoices/{id}/pdf` | Download PDF |
| | POST | `/api/invoices/{id}/issue` | Mark issued |
| | POST | `/api/invoices/{id}/mark-paid` | Mark paid |
| **Analytics** | GET | `/api/analytics/dashboard` | Dashboard stats |
| | GET | `/api/analytics/vendor-performance` | Vendor metrics |
| | GET | `/api/analytics/monthly-trends` | Monthly trends |
| | GET | `/api/analytics/spending` | Spending breakdown |
| **Notifications** | GET | `/api/notifications/my` | User notifications |
| | PUT | `/api/notifications/{id}/read` | Mark read |
| | PUT | `/api/notifications/mark-all-read` | Mark all read |
| **Activity Logs** | GET | `/api/activity-logs` | Audit trail (Admin) |
| **WebSocket** | WS | `/api/ws/notifications` | Real-time stream |

---

## Role-Based Access Control

### 4 Roles with Granular Permissions

| Feature | Procurement Officer | Vendor | Manager | Admin |
|---|:---:|:---:|:---:|:---:|
| View Dashboard | Full | Limited | Full | Full |
| Manage Vendors | Create/Edit | - | View | Full |
| Create RFQs | Yes | - | - | Yes |
| Submit Quotations | - | Yes | - | - |
| Compare Quotations | Yes | - | Yes | Yes |
| Request Approval | Yes | - | - | Yes |
| Approve/Reject | - | - | Yes | Yes |
| Generate POs | Yes | - | - | Yes |
| Generate Invoices | Yes | - | - | Yes |
| Download PDF | Yes | - | Yes | Yes |
| View Activity Logs | Own | Own | - | All |
| View Reports | Yes | - | Yes | Yes |
| Admin Settings | - | - | - | Yes |

---

## Key Features

### Security
- JWT access tokens (15-min) + refresh token rotation (7-day)
- Bcrypt password hashing (12 rounds, 72-byte safe)
- Account locking after 5 failed login attempts (30-min cooldown)
- Two-factor authentication via email OTP
- Rate limiting on auth endpoints (5/min login, 3/hr verification)
- Indian GST number format validation (15-char regex)
- Input sanitization via Pydantic schemas

### PDF Invoice Generation
- Professional layout using ReportLab
- Company branding header with GSTIN
- Bill-to section with vendor details
- Formatted line items table
- Tax breakdown (18% GST)
- Grand total with styling
- Saved to disk and available for download

### Email System (Brevo API)
- Account verification emails
- Password reset links
- 2FA OTP delivery
- Invoice email with PDF attachment
- VendorBridge branded HTML templates

### Real-Time Notifications
- WebSocket connections with JWT auth
- Per-user message delivery
- Multi-tab support
- Ping/pong keepalive
- Notification types: INFO, WARNING, SUCCESS, ERROR

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ 
- Node.js 22+ (or Bun 1.0+)
- Git

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/choksi2212/vendor-odoo.git
cd vendor-odoo

# 2. Setup Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# 3. Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE vendorbridge;"

# 4. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL password and Brevo API key

# 5. Create database tables
python -c "from app.db.base import Base; from app.db.session import engine; from app.models import *; Base.metadata.create_all(bind=engine)"

# 6. Seed demo data (optional)
python seed_full_demo.py

# 7. Start backend server
uvicorn app.main:app --reload --port 8000

# 8. Setup Frontend (new terminal)
cd ../frontend
npm install         # or: bun install
npm run dev         # or: bun run dev

# 9. Open in browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Default Test Accounts

| Role | Email | Password |
|---|---|---|
| Procurement Officer | officer@vendorbridge.com | Officer123! |
| Manager | manager@vendorbridge.com | Manager123! |
| Admin | admin@vendorbridge.com | Admin1234! |

---

## Running Tests

```bash
cd backend
.venv\Scripts\activate
pytest tests/ -v

# Expected: 232 passed
```

### Test Coverage

| Module | Tests | What's Tested |
|---|---|---|
| Authentication | 43 | Signup (all roles, validation), login, token refresh, 2FA, password reset, account locking |
| Vendors | 41 | CRUD, GST validation, search, filter, pagination, RBAC |
| RFQs | 34 | CRUD, lifecycle (draft/open/closed), vendor assignment, publish |
| Quotations | 22 | Create, submit, comparison analytics, duplicate prevention |
| Approvals | 20 | Create, approve, reject, history timeline, separation of duties |
| Purchase Orders | 17 | Auto-generation, sequential numbering, tax calculation |
| Invoices | 16 | Creation, PDF generation (real output), status workflow |
| Analytics | 23 | Dashboard, vendor performance, trends, notifications |
| WebSocket | 16 | Connection, auth, messaging, notification service |

---

## Security Implementation

```
Request Flow with Security Layers:

  Client Request
       │
       ▼
  ┌─────────────┐
  │  CORS Check │  (Origin validation)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Rate Limiter│  (SlowAPI - per IP)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  JWT Verify │  (Access token validation)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Role Guard  │  (Permission check)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Pydantic   │  (Input validation + sanitization)
  │  Schema     │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Service    │  (Business logic + DB transaction)
  │  Layer      │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Activity   │  (Audit log with IP + user-agent)
  │  Logger     │
  └─────────────┘
```

---

## Deployment

### Backend (Railway)

The backend includes `Procfile`, `nixpacks.toml`, `railway.json`, and `Dockerfile` for easy deployment:

```bash
# Railway auto-deploys on git push
git push origin main
```

### Frontend (Vercel/Netlify)

```bash
cd frontend
npm run build    # Creates optimized production build
# Deploy the dist/ folder
```

### Environment Variables (Production)

```env
DATABASE_URL=postgresql://user:pass@host:5432/vendorbridge
SECRET_KEY=<64-char-hex-string>
BREVO_API_KEY=<your-brevo-key>
BREVO_SENDER_EMAIL=<verified-sender>
ALLOWED_ORIGINS=["https://your-frontend.vercel.app"]
APP_BASE_URL=https://your-frontend.vercel.app
```

---

## Hackathon Evaluation Criteria

| Criteria | Our Implementation |
|---|---|
| **Database Design** | 18 normalized tables, UUID PKs, proper FKs, indexes, constraints |
| **Coding Standards** | PEP8 Python, TypeScript strict, service layer pattern, DRY |
| **Modularity** | Layered architecture (API -> Service -> Model -> DB) |
| **Frontend Design** | Enterprise ERP UI, Tailwind design system, consistent components |
| **Performance** | Async FastAPI, connection pooling, indexed queries, code splitting |
| **Scalability** | Stateless JWT, PostgreSQL, WebSocket, containerized |
| **Security** | Bcrypt, JWT rotation, account locking, rate limiting, RBAC |
| **Usability** | Role-based navigation, real-time feedback, loading states |
| **Real-Time Data** | Live PostgreSQL queries, WebSocket notifications |
| **Input Validation** | Pydantic (backend) + Zod (frontend), GST regex, password policy |
| **Git Usage** | Meaningful commits, proper branching, clean history |
| **Attention to Detail** | Indian GST format, sequential PO/INV numbering, tax calculations |

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

<div align="center">

**Built for the Odoo x KSV Hackathon 2026**

*Enterprise Procurement Management — Digitized, Streamlined, Secured.*

</div>
