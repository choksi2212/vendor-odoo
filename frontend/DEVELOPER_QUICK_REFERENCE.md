# Developer Quick Reference - VendorBridge Integration

**Last Updated:** June 6, 2026  
**Integration Status:** 61% Complete (11/18 pages)

---

## 🚦 CURRENT STATUS

### ✅ Complete & Working:
- Authentication (Login, Signup)
- Dashboard
- Vendors (List, Add)
- RFQs (List, Create, Detail, Compare) ⭐
- Quotations (List, Submit)

### ⏳ Pending:
- Approvals
- Purchase Orders
- Invoices
- Activity Logs
- Reports
- Additional auth pages (OTP, Password Reset)

---

## 📁 PROJECT STRUCTURE

```
src/
├── lib/
│   ├── api/
│   │   ├── client.ts          # API client with token management
│   │   ├── endpoints.ts       # All API endpoint functions
│   │   ├── transform.ts       # snake_case ↔ camelCase
│   │   └── websocket.ts       # WebSocket client
│   └── config.ts              # Environment config
├── context/
│   └── AuthContext.tsx        # Authentication state
├── routes/
│   ├── login.tsx              # ✅ Integrated
│   ├── signup.tsx             # ✅ Integrated
│   ├── dashboard.tsx          # ✅ Integrated
│   ├── vendors/
│   │   ├── index.tsx          # ✅ Integrated
│   │   └── add.tsx            # ✅ Integrated
│   ├── rfq/
│   │   ├── index.tsx          # ✅ Integrated
│   │   ├── create.tsx         # ✅ Integrated
│   │   └── $id/
│   │       ├── index.tsx      # ✅ Integrated
│   │       └── compare.tsx    # ✅ Integrated ⭐
│   ├── quotations/
│   │   ├── index.tsx          # ✅ Integrated
│   │   └── submit/$rfqId.tsx  # ✅ Integrated
│   ├── approvals.tsx          # ⏳ TODO
│   ├── purchase-orders/       # ⏳ TODO
│   ├── invoices/              # ⏳ TODO
│   ├── activity-logs.tsx      # ⏳ TODO
│   └── reports.tsx            # ⏳ TODO
└── data/
    └── mockData.ts            # Mock data (still used by pending pages)
```

---

## 🔌 API CLIENT USAGE

### Basic Pattern:
```typescript
import { apiName } from "@/lib/api/endpoints";

// In component:
const [data, setData] = useState<Type[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState("");

const loadData = async () => {
  try {
    setLoading(true);
    setError("");
    const result = await apiName.method(params);
    setData(result);
  } catch (err: any) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};
```

### Available APIs:
```typescript
// Authentication
authAPI.login(credentials)
authAPI.signup(userData)
authAPI.logout()
authAPI.refresh()

// Vendors
vendorAPI.list(params)
vendorAPI.create(vendorData)
vendorAPI.getCategories()

// RFQs
rfqAPI.list(params)
rfqAPI.create(rfqData)
rfqAPI.getById(id)
rfqAPI.assignVendors(rfqId, vendorIds)

// Quotations
quotationAPI.list(params)
quotationAPI.create(quotationData)
quotationAPI.submit(id)
quotationAPI.listForRFQ(rfqId)
quotationAPI.compareForRFQ(rfqId)

// Approvals (defined, not yet used)
approvalAPI.list(params)
approvalAPI.approve(id)
approvalAPI.reject(id, reason)

// Purchase Orders (defined, not yet used)
poAPI.list(params)
poAPI.create(poData)
poAPI.getById(id)

// Invoices (defined, not yet used)
invoiceAPI.list(params)
invoiceAPI.create(invoiceData)
invoiceAPI.getById(id)
invoiceAPI.downloadPDF(id)

// Analytics
analyticsAPI.getDashboard()
```

---

## 🎨 UI PATTERNS

### Loading State:
```tsx
{loading && (
  <div className="flex items-center justify-center py-12">
    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
    Loading...
  </div>
)}
```

### Error State:
```tsx
{error && (
  <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
    <div className="flex items-center gap-2">
      <AlertCircle className="h-5 w-5" />
      <span className="font-medium">{error}</span>
    </div>
    <Button onClick={loadData} className="mt-3">Retry</Button>
  </div>
)}
```

### Empty State:
```tsx
{data.length === 0 && (
  <div className="rounded-lg border border-dashed border-border bg-muted/20 p-12 text-center">
    <p className="text-muted-foreground">No items found.</p>
  </div>
)}
```

### Debounced Search:
```tsx
const [search, setSearch] = useState("");

useEffect(() => {
  const timer = setTimeout(() => {
    if (!loading) loadData();
  }, 300);
  return () => clearTimeout(timer);
}, [search]);
```

---

## 🧪 COMMON TASKS

### Adding a New Page:

1. **Create route file:**
```bash
src/routes/new-page.tsx
```

2. **Basic template:**
```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { apiName } from "@/lib/api/endpoints";
import { Loader2, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/new-page")({
  component: NewPage
});

interface DataType {
  id: string;
  // ... fields
}

function NewPage() {
  const [data, setData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      const result = await apiName.list();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <PageHeader title="Page Title" />
      {/* Loading, Error, Empty, Data states */}
    </Layout>
  );
}
```

3. **Add to sidebar** (if needed):
```tsx
// src/components/Sidebar.tsx
const menuItems = [
  // ...
  { path: '/new-page', label: 'New Page', icon: Icon, roles: ['all'] },
];
```

---

## 🔐 AUTHENTICATION

### Check if authenticated:
```tsx
import { useAuth } from "@/context/AuthContext";

const { isAuthenticated, user, role } = useAuth();

if (!isAuthenticated) {
  // Redirect to login (handled by router)
}
```

### Role-based rendering:
```tsx
const { user } = useAuth();

{user?.role === "procurement_officer" && (
  <Button>Create RFQ</Button>
)}
```

### Backend roles:
- `procurement_officer`
- `vendor`
- `manager`
- `admin`

---

## 🎯 FORM PATTERNS

### Basic form:
```tsx
const [formData, setFormData] = useState({
  field1: "",
  field2: 0,
});
const [submitting, setSubmitting] = useState(false);
const [error, setError] = useState("");

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError("");
  
  // Validation
  if (!formData.field1) {
    setError("Field 1 is required");
    return;
  }
  
  try {
    setSubmitting(true);
    await apiName.create(formData);
    nav({ to: "/success" });
  } catch (err: any) {
    setError(err.message);
    setSubmitting(false);
  }
};

return (
  <form onSubmit={handleSubmit}>
    <Field label="Field 1">
      <input
        className={inputCls}
        value={formData.field1}
        onChange={(e) => setFormData(prev => ({
          ...prev,
          field1: e.target.value
        }))}
        required
      />
    </Field>
    
    <Button type="submit" disabled={submitting}>
      {submitting ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Submitting...
        </>
      ) : (
        "Submit"
      )}
    </Button>
  </form>
);
```

---

## 📋 CHECKLIST FOR NEW PAGES

### Before you start:
- [ ] Read integration guide section for this page
- [ ] Check if API endpoints exist in `endpoints.ts`
- [ ] Identify data types needed
- [ ] Plan component structure

### During implementation:
- [ ] Create TypeScript interfaces
- [ ] Add loading state
- [ ] Add error state
- [ ] Add empty state
- [ ] Add form validation (if form)
- [ ] Test with mock data first
- [ ] Replace with real API calls
- [ ] Add retry mechanism
- [ ] Format dates/numbers properly
- [ ] Add role-based logic (if needed)

### After implementation:
- [ ] Test loading state
- [ ] Test error state
- [ ] Test empty state
- [ ] Test form submission (if form)
- [ ] Test navigation
- [ ] Check console for errors
- [ ] Verify TypeScript (no errors)
- [ ] Update documentation

---

## 🐛 COMMON ISSUES & SOLUTIONS

### Issue: "Cannot read property of undefined"
**Solution:** Add null checks:
```tsx
{data?.field || "Default"}
{data && data.length > 0 && <Component />}
```

### Issue: API returns snake_case
**Solution:** Already handled! `snakeToCamel()` in client.ts

### Issue: Need to reload data after action
**Solution:**
```tsx
const handleAction = async () => {
  await apiName.action();
  loadData(); // Reload list
};
```

### Issue: Token expired
**Solution:** Already handled! Auto-refresh in client.ts

### Issue: Form submits but data doesn't update
**Solution:** Make sure to call `loadData()` or navigate away

---

## 🔍 DEBUGGING TIPS

### Check API calls:
1. Open browser DevTools → Network tab
2. Look for API calls
3. Check request payload (snake_case)
4. Check response (snake_case → auto-converted)
5. Check for 401 (auth issue), 400 (validation), 500 (server error)

### Check state:
```tsx
console.log("Data:", data);
console.log("Loading:", loading);
console.log("Error:", error);
```

### Check transforms:
```tsx
import { snakeToCamel, camelToSnake } from "@/lib/api/transform";

console.log(snakeToCamel({ user_name: "John" })); // { userName: "John" }
console.log(camelToSnake({ userName: "John" })); // { user_name: "John" }
```

---

## 📚 USEFUL REFERENCES

### Documentation:
- `INTEGRATION_COMPLETE_STATUS.md` - Overall status
- `RFQ_INTEGRATION_COMPLETE.md` - RFQ module guide
- `QUOTATION_INTEGRATION_COMPLETE.md` - Quotation module guide
- `FRONTEND_BACKEND_INTEGRATION_GUIDE.md` - Complete integration guide

### Code Examples:
- `src/routes/rfq/index.tsx` - List with search/filter
- `src/routes/rfq/create.tsx` - Form with validation
- `src/routes/rfq/$id/index.tsx` - Detail page
- `src/routes/rfq/$id/compare.tsx` - Complex table with sorting
- `src/routes/quotations/submit/$rfqId.tsx` - Two-step submission

---

## 🚀 QUICK START

### To run locally:
```bash
# Backend
cd backend
.\.venv\Scripts\activate  # Windows
uvicorn app.main:app --reload

# Frontend
cd vendorflow-bridge-main
bun install
bun run dev
```

### To test:
1. Open http://localhost:5173
2. Signup with test account
3. Login
4. Navigate to integrated pages
5. Test workflows

---

## 💡 PRO TIPS

1. **Always add loading states** - Users need feedback
2. **Always handle errors** - Don't let the app crash
3. **Always validate forms** - Prevent bad data
4. **Use TypeScript** - Catch bugs early
5. **Follow patterns** - Look at existing pages
6. **Test as you go** - Don't wait until the end
7. **Document as you code** - Future you will thank you
8. **Use descriptive names** - Code is read more than written
9. **Keep components small** - Easier to understand and test
10. **Don't repeat yourself** - Extract reusable logic

---

## 🎓 LEARNING RESOURCES

### If you need to understand:
- **TanStack Router:** https://tanstack.com/router
- **React Hooks:** https://react.dev/reference/react
- **TypeScript:** https://www.typescriptlang.org/docs/
- **Tailwind CSS:** https://tailwindcss.com/docs
- **REST APIs:** MDN Web Docs

### Internal patterns:
- Read `src/lib/api/client.ts` for token management
- Read `src/context/AuthContext.tsx` for auth flow
- Read `src/routes/rfq/create.tsx` for complex forms
- Read `src/routes/rfq/$id/compare.tsx` for advanced tables

---

**Remember:** If you're stuck, look at similar completed pages. Patterns are consistent!

**Good luck!** 🚀
