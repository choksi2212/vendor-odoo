<div align="center">

<img src="https://img.shields.io/badge/VendorBridge-ERP-0F172A?style=for-the-badge&logo=buffer&logoColor=white" alt="VendorBridge" />

# VendorBridge ERP

### Procurement & Vendor Management System

[![React](https://img.shields.io/badge/React_19-20232A?style=flat-square&logo=react&logoColor=61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Bun](https://img.shields.io/badge/Bun-000000?style=flat-square&logo=bun&logoColor=white)](https://bun.sh/)
[![Radix UI](https://img.shields.io/badge/Radix_UI-161618?style=flat-square&logo=radix-ui&logoColor=white)](https://www.radix-ui.com/)
[![License](https://img.shields.io/badge/License-Hackathon-blue?style=flat-square)](./LICENSE)
[![Hackathon](https://img.shields.io/badge/Odoo_×_KSV-Hackathon_2024-8B5CF6?style=flat-square&logo=odoo&logoColor=white)](https://github.com)

<br/>

> A comprehensive ERP solution that digitizes and streamlines the complete procurement lifecycle —  
> from vendor onboarding through invoice dispatch — with structured workflows and role-based access control.

<br/>

</div>

---

## 🎯 Problem Statement

Organizations waste time and resources on manual, fragmented procurement processes:

| Pain Point | Impact |
|---|---|
| Vendors managed via spreadsheets / email | Zero traceability, frequent errors |
| No structured RFQ → Approval → PO pipeline | Delayed procurement cycles |
| No quotation comparison mechanism | Suboptimal vendor selection |
| No audit trail or activity logs | Compliance and accountability gaps |

**VendorBridge** eliminates all of this through a single, centralized procurement platform.

---

## 🔄 Core Business Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     VENDORBRIDGE WORKFLOW                           │
└─────────────────────────────────────────────────────────────────────┘

  [Procurement Officer]          [Vendor]              [Manager]
         │                          │                      │
         ▼                          │                      │
   ① Create RFQ                     │                      │
         │                          │                      │
         ▼                          │                      │
   ② Invite Vendors ──────────► ③ Submit Quotations       │
                                    │                      │
         ◄──────────────────────────┘                      │
         │                                                  │
         ▼                                                  │
   ④ Compare Quotations                                     │
         │                                                  │
         ▼                                                  │
   ⑤ Initiate Approval ──────────────────────────────► ⑥ Approve / Reject
                                                            │
         ◄──────────────────────────────────────────────────┘
         │
         ▼
   ⑦ Generate Purchase Order (Auto PO#)
         │
         ▼
   ⑧ Generate Invoice from PO
         │
         ├──► 📄 Download PDF
         ├──► 🖨️  Print Invoice
         └──► 📧 Send via Email
                    │
                    ▼
         📊 Activity Logged → Analytics Updated
```

---

## 🏗️ Implementation Architecture

```
vendorbridge/
├── src/
│   ├── components/              # Reusable UI primitives
│   │   ├── Sidebar.jsx          # Role-aware nav sidebar
│   │   ├── Topbar.jsx           # Global topbar with user context
│   │   ├── Layout.jsx           # Page wrapper (sidebar + topbar)
│   │   ├── Table.jsx            # Enterprise data table component
│   │   ├── StatCard.jsx         # Dashboard metric cards
│   │   ├── Badge.jsx            # Status pill badges
│   │   └── Button.jsx           # Standardized button variants
│   │
│   ├── pages/                   # Route-level page components
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   ├── ForgotPassword.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Vendors/
│   │   │   ├── VendorList.jsx
│   │   │   ├── VendorAdd.jsx
│   │   │   ├── VendorView.jsx
│   │   │   └── VendorEdit.jsx
│   │   ├── RFQ/
│   │   │   ├── RFQList.jsx
│   │   │   ├── RFQCreate.jsx
│   │   │   ├── RFQView.jsx
│   │   │   └── RFQCompare.jsx
│   │   ├── Quotations/
│   │   │   ├── QuotationList.jsx
│   │   │   └── QuotationSubmit.jsx
│   │   ├── Approvals/
│   │   │   └── ApprovalWorkflow.jsx
│   │   ├── PurchaseOrders/
│   │   │   ├── POList.jsx
│   │   │   └── POView.jsx
│   │   ├── Invoices/
│   │   │   ├── InvoiceList.jsx
│   │   │   ├── InvoiceView.jsx
│   │   │   └── InvoiceCreate.jsx
│   │   ├── ActivityLogs.jsx
│   │   ├── Reports.jsx
│   │   └── Settings.jsx         # Admin only
│   │
│   ├── context/
│   │   └── AuthContext.jsx      # Role state (mock, no real auth)
│   │
│   ├── data/                    # Static mock data
│   │   ├── mockVendors.js
│   │   ├── mockRFQs.js
│   │   ├── mockQuotations.js
│   │   ├── mockApprovals.js
│   │   ├── mockPOs.js
│   │   ├── mockInvoices.js
│   │   └── mockLogs.js
│   │
│   ├── hooks/                   # Custom React hooks
│   ├── lib/                     # Utility functions and helpers
│   ├── router.tsx               # TanStack Router config (all routes)
│   └── styles.css               # Global styles + CSS variables
│
├── package.json
├── vite.config.ts
└── README.md
```

### Data Flow Architecture

```
AuthContext (Role State)
       │
       ▼
   App Router (TanStack Router)
       │
       ├── Public Routes      →  /login, /signup, /forgot-password
       │
       └── Protected Routes   →  Layout (Sidebar + Topbar)
                                      │
                                      ├── /dashboard
                                      ├── /vendors/*
                                      ├── /rfq/*
                                      ├── /quotations/*
                                      ├── /approvals
                                      ├── /purchase-orders/*
                                      ├── /invoices/*
                                      ├── /activity-logs
                                      ├── /reports
                                      └── /settings  (Admin only)
```

### Role-Based Access Matrix

| Route | Procurement Officer | Vendor | Manager | Admin |
|---|:---:|:---:|:---:|:---:|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Vendor Management | ✅ | ❌ | ❌ | ✅ |
| RFQ Management | ✅ | ❌ | ❌ | ✅ |
| Quotation Submission | ❌ | ✅ | ❌ | ❌ |
| Quotation Comparison | ✅ | ❌ | ❌ | ✅ |
| Approval Workflow | ❌ | ❌ | ✅ | ✅ |
| Purchase Orders | ✅ | ✅ (view) | ✅ | ✅ |
| Invoices | ✅ | ❌ | ✅ | ✅ |
| Activity Logs | ✅ | ✅ | ❌ | ✅ |
| Reports & Analytics | ✅ | ❌ | ✅ | ✅ |
| Admin Settings | ❌ | ❌ | ❌ | ✅ |

---

## ✨ Key Features

<details>
<summary><b>Vendor Management</b></summary>

- Complete vendor registration (Name, Category, GST, Contact info)
- Vendor status tracking (Active / Inactive)
- Search and category-based filter
- Full CRUD: Add, View, Edit vendors

</details>

<details>
<summary><b>RFQ Management</b></summary>

- Create detailed RFQs with product/service specifications
- Deadline tracking with visual indicators
- Targeted vendor assignment (multi-select)
- Status lifecycle: Draft → Open → Closed

</details>

<details>
<summary><b>Quotation System</b></summary>

- Vendor-facing quotation submission form
- Side-by-side quotation comparison table
- Lowest price auto-highlighted in green
- Fastest delivery auto-highlighted in blue
- Vendor rating indicators

</details>

<details>
<summary><b>Approval Workflow</b></summary>

- Structured approval hierarchy (Manager gate)
- Approve / Reject with inline remarks
- Visual approval timeline stepper
- State transitions: Pending → Approved / Rejected

</details>

<details>
<summary><b>Purchase Orders & Invoicing</b></summary>

- Auto-generated PO numbers (PO-YYYY-XXX format)
- Invoice generation directly from approved POs
- Tax calculation with line item breakdown
- PDF download via `window.print()`
- Email dispatch (mock alert with vendor email)
- Status lifecycle: Draft → Issued → Paid

</details>

<details>
<summary><b>Analytics & Reporting</b></summary>

- Real-time dashboard stat cards
- Vendor performance metrics table
- Monthly procurement spend bar chart (SVG)
- Exportable report (mock)
- Complete activity log with audit trail

</details>

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | React 19 |
| **Routing** | TanStack Router |
| **Styling** | Tailwind CSS |
| **UI Components** | Radix UI |
| **Forms** | React Hook Form + Zod |
| **State / Data** | TanStack Query |
| **Charts** | Recharts |
| **Build Tool** | Vite |
| **Package Manager** | Bun |

---

##  Getting Started

### Prerequisites

- Node.js 18+ **or** Bun 1.0+
- Any modern web browser

### Installation & Run

```bash
# Clone the repository
git clone https://github.com/hemathens/vendorbridge.git
cd vendorbridge

# Install dependencies
bun install

# Start development server
bun run dev
```

### All Commands

```bash
bun run dev       # Start dev server (localhost:5173)
bun run build     # Production build
bun run preview   # Preview production build
bun run lint      # Run ESLint
bun run format    # Format with Prettier
```

---

## 🎨 Design System

| Token | Value | Usage |
|---|---|---|
| Primary Dark | `#0F172A` | Sidebar, headings |
| Action Blue | `#2563EB` | Buttons, links, active states |
| Success Green | `#16A34A` | Active / Approved badges |
| Warning Yellow | `#CA8A04` | Pending badges |
| Danger Red | `#DC2626` | Rejected badges |
| Draft Blue | `#2563EB` | Draft status badges |
| Font — Headings | `Sora` | Page titles, section headers |
| Font — Body | `DM Sans` | All body text, tables, forms |

---

## 🏆 Hackathon Highlights

1. **Complete End-to-End Workflow** — Full 8-step procurement cycle, demo-ready
2. **Role-Based Access Control** — 4 distinct roles with separate nav and permissions
3. **Advanced Quotation Comparison** — Visual side-by-side table with auto-highlighting
4. **PDF & Email Invoice Delivery** — Print-ready invoice layout with send simulation
5. **Real-Time Analytics Dashboard** — SVG bar charts, stat cards, vendor performance table
6. **Clean Module Architecture** — Proper ERP component structure and data separation

---

## 👥 Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/hemathens">
        <img src="https://github.com/hemathens.png" width="80px" style="border-radius:50%" alt="hemathens"/><br/>
        <sub><b>Hem Patel</b></sub>
      </a><br/>
      <sub>Frontend Architecture · RFQ & Approval Modules · Dashboard</sub>
    </td>
    <td align="center">
      <a href="https://github.com/choksi2212">
        <img src="https://github.com/choksi2212.png" width="80px" style="border-radius:50%" alt="choksi2212"/><br/>
        <sub><b>Manas Choksi</b></sub>
      </a><br/>
      <sub>Backend Architecture · Invoice Module · UX Components</sub>
    </td>
  </tr>
</table>

---

## 📝 License

This project was developed for the **Odoo × KSV Hackathon 2024**.  
All rights reserved by the contributors.

---

<div align="center">

**Built with precision for the Odoo × KSV Hackathon**

[![hemathens](https://img.shields.io/badge/GitHub-hemathens-181717?style=flat-square&logo=github)](https://github.com/hemathens)
[![choksi2212](https://img.shields.io/badge/GitHub-choksi2212-181717?style=flat-square&logo=github)](https://github.com/choksi2212)

*Transforming Procurement Management — One Workflow at a Time*

</div>
