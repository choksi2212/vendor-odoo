export const mockRFQs = [
  { id: "RFQ-2026-001", title: "Annual Office Stationery Procurement", description: "Bulk stationery supplies for HQ for FY26.", product: "Stationery Kit", quantity: 500, unit: "kits", deadline: "2026-06-20", vendors: ["Crescent Office Solutions", "Pioneer Packaging Mills"], status: "Open" },
  { id: "RFQ-2026-002", title: "Server Rack Hardware Refresh", description: "42U racks with PDUs and rail kits.", product: "42U Server Rack", quantity: 12, unit: "units", deadline: "2026-06-15", vendors: ["Acme Industrial Supplies", "Helios IT Systems"], status: "Open" },
  { id: "RFQ-2026-003", title: "Industrial Solvent Supply Q3", description: "ISO certified solvent, quarterly contract.", product: "Industrial Solvent IS-440", quantity: 2000, unit: "litres", deadline: "2026-06-10", vendors: ["Vertex Chemicals Co."], status: "Closed" },
  { id: "RFQ-2026-004", title: "Last-Mile Delivery Partner Onboarding", description: "Tier-2 city delivery network expansion.", product: "Logistics Services", quantity: 1, unit: "contract", deadline: "2026-06-25", vendors: ["Northwind Logistics Pvt Ltd"], status: "Draft" },
  { id: "RFQ-2026-005", title: "Laptop Refresh Program — Engineering", description: "Developer-grade laptops with 3yr warranty.", product: "Engineering Laptop", quantity: 80, unit: "units", deadline: "2026-07-01", vendors: ["Helios IT Systems", "Acme Industrial Supplies"], status: "Open" },
];

export const mockQuotations = [
  { id: "Q-001", rfqId: "RFQ-2026-002", vendor: "Acme Industrial Supplies", unitPrice: 48500, quantity: 12, total: 582000, deliveryDays: 21, rating: 4.6, status: "Submitted", notes: "Includes installation support", warranty: "2 years", certifications: "ISO 9001" },
  { id: "Q-002", rfqId: "RFQ-2026-002", vendor: "Helios IT Systems", unitPrice: 46200, quantity: 12, total: 554400, deliveryDays: 14, rating: 4.7, status: "Submitted", notes: "Express delivery available", warranty: "3 years", certifications: "ISO 9001, ISO 27001" },
  { id: "Q-007", rfqId: "RFQ-2026-002", vendor: "TechSupply Corp", unitPrice: 44800, quantity: 12, total: 537600, deliveryDays: 18, rating: 4.4, status: "Submitted", notes: "Bulk discount applied", warranty: "2 years", certifications: "ISO 9001" },
  { id: "Q-003", rfqId: "RFQ-2026-001", vendor: "Crescent Office Solutions", unitPrice: 1850, quantity: 500, total: 925000, deliveryDays: 18, rating: 4.2, status: "Submitted", notes: "Premium quality supplies", warranty: "1 year", certifications: "ISO 9001" },
  { id: "Q-004", rfqId: "RFQ-2026-001", vendor: "Pioneer Packaging Mills", unitPrice: 1990, quantity: 500, total: 995000, deliveryDays: 12, rating: 4.1, status: "Submitted", notes: "Fast delivery guaranteed", warranty: "6 months", certifications: "ISO 9001" },
  { id: "Q-008", rfqId: "RFQ-2026-001", vendor: "Office Mart India", unitPrice: 1750, quantity: 500, total: 875000, deliveryDays: 20, rating: 4.3, status: "Submitted", notes: "Eco-friendly packaging", warranty: "1 year", certifications: "ISO 9001, FSC" },
  { id: "Q-005", rfqId: "RFQ-2026-005", vendor: "Helios IT Systems", unitPrice: 92500, quantity: 80, total: 7400000, deliveryDays: 28, rating: 4.7, status: "Submitted", notes: "Pre-configured with software", warranty: "3 years", certifications: "ISO 27001" },
  { id: "Q-006", rfqId: "RFQ-2026-005", vendor: "Acme Industrial Supplies", unitPrice: 95000, quantity: 80, total: 7600000, deliveryDays: 21, rating: 4.6, status: "Submitted", notes: "On-site deployment support", warranty: "3 years", certifications: "ISO 9001" },
  { id: "Q-009", rfqId: "RFQ-2026-005", vendor: "TechSupply Corp", unitPrice: 89900, quantity: 80, total: 7192000, deliveryDays: 25, rating: 4.4, status: "Submitted", notes: "Extended warranty option", warranty: "4 years", certifications: "ISO 27001" },
];

export const myVendorQuotations = [
  { rfqId: "RFQ-2026-002", rfqTitle: "Server Rack Hardware Refresh", status: "Submitted", myPrice: 46200, deliveryDays: 14 },
  { rfqId: "RFQ-2026-005", rfqTitle: "Laptop Refresh Program — Engineering", status: "Open", myPrice: null, deliveryDays: null },
  { rfqId: "RFQ-2026-004", rfqTitle: "Last-Mile Delivery Partner Onboarding", status: "Open", myPrice: null, deliveryDays: null },
];

export const mockApprovals = [
  { id: "AP-001", rfqId: "RFQ-2026-002", rfqTitle: "Server Rack Hardware Refresh", vendor: "Helios IT Systems", amount: 554400, submittedBy: "Alex Morgan", date: "2026-06-04", status: "Pending" },
  { id: "AP-002", rfqId: "RFQ-2026-001", rfqTitle: "Annual Office Stationery Procurement", vendor: "Crescent Office Solutions", amount: 925000, submittedBy: "Alex Morgan", date: "2026-06-03", status: "Pending" },
  { id: "AP-003", rfqId: "RFQ-2026-003", rfqTitle: "Industrial Solvent Supply Q3", vendor: "Vertex Chemicals Co.", amount: 1840000, submittedBy: "Priya Shah", date: "2026-05-28", status: "Approved" },
  { id: "AP-004", rfqId: "RFQ-2026-005", rfqTitle: "Laptop Refresh — Eng", vendor: "Acme Industrial Supplies", amount: 7600000, submittedBy: "Alex Morgan", date: "2026-05-25", status: "Rejected" },
];

export const mockPOs = [
  { id: "PO-2026-001", vendor: "Vertex Chemicals Co.", rfqId: "RFQ-2026-003", amount: 1840000, date: "2026-05-29", status: "Issued",
    items: [{ product: "Industrial Solvent IS-440", qty: 2000, unitPrice: 920, total: 1840000 }], tax: 331200 },
  { id: "PO-2026-002", vendor: "Helios IT Systems", rfqId: "RFQ-2026-002", amount: 554400, date: "2026-06-05", status: "Draft",
    items: [{ product: "42U Server Rack", qty: 12, unitPrice: 46200, total: 554400 }], tax: 99792 },
  { id: "PO-2026-003", vendor: "Crescent Office Solutions", rfqId: "RFQ-2026-001", amount: 925000, date: "2026-06-05", status: "Issued",
    items: [{ product: "Stationery Kit", qty: 500, unitPrice: 1850, total: 925000 }], tax: 166500 },
  { id: "PO-2026-004", vendor: "Northwind Logistics Pvt Ltd", rfqId: "RFQ-2026-004", amount: 480000, date: "2026-05-20", status: "Issued",
    items: [{ product: "Logistics Services (Annual)", qty: 1, unitPrice: 480000, total: 480000 }], tax: 86400 },
];

export const mockInvoices = [
  { id: "INV-2026-001", poId: "PO-2026-001", vendor: "Vertex Chemicals Co.", amount: 1840000, tax: 331200, total: 2171200, date: "2026-05-30", status: "Paid" },
  { id: "INV-2026-002", poId: "PO-2026-003", vendor: "Crescent Office Solutions", amount: 925000, tax: 166500, total: 1091500, date: "2026-06-06", status: "Issued" },
  { id: "INV-2026-003", poId: "PO-2026-004", vendor: "Northwind Logistics Pvt Ltd", amount: 480000, tax: 86400, total: 566400, date: "2026-05-22", status: "Issued" },
  { id: "INV-2026-004", poId: "PO-2026-002", vendor: "Helios IT Systems", amount: 554400, tax: 99792, total: 654192, date: "2026-06-06", status: "Draft" },
];

export const mockLogs = [
  { ts: "2026-06-06 09:42", user: "Alex Morgan", action: "Created RFQ", entity: "RFQ-2026-005", category: "RFQ", details: "Laptop Refresh — Engineering" },
  { ts: "2026-06-06 09:15", user: "System", action: "Generated PO", entity: "PO-2026-003", category: "Invoice", details: "Auto-generated from approval" },
  { ts: "2026-06-05 18:02", user: "Priya Shah", action: "Approved", entity: "AP-003", category: "Approval", details: "Solvent supply Q3" },
  { ts: "2026-06-05 16:48", user: "Helios IT Systems", action: "Submitted quotation", entity: "Q-002", category: "RFQ", details: "RFQ-2026-002" },
  { ts: "2026-06-05 14:30", user: "Crescent Office", action: "Submitted quotation", entity: "Q-003", category: "RFQ", details: "RFQ-2026-001" },
  { ts: "2026-06-05 11:11", user: "Alex Morgan", action: "Sent Invoice Email", entity: "INV-2026-001", category: "Invoice", details: "Sent to billing@vertexchem.com" },
  { ts: "2026-06-04 17:55", user: "Alex Morgan", action: "Initiated approval", entity: "AP-001", category: "Approval", details: "Server rack refresh" },
  { ts: "2026-06-04 12:09", user: "Acme Industrial", action: "Submitted quotation", entity: "Q-001", category: "RFQ", details: "RFQ-2026-002" },
  { ts: "2026-06-03 10:21", user: "Alex Morgan", action: "Created RFQ", entity: "RFQ-2026-002", category: "RFQ", details: "Server Rack Hardware Refresh" },
  { ts: "2026-05-30 09:00", user: "System", action: "Invoice marked Paid", entity: "INV-2026-001", category: "Invoice", details: "Bank reconciliation" },
];
