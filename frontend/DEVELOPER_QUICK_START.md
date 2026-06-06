# VendorBridge Frontend - Developer Quick Start

> Get up and running in 5 minutes ⚡

---

## 🚀 Installation

```bash
# Clone the repository
cd vendorflow-bridge-main

# Install dependencies (using Bun - fastest)
bun install

# Start development server
bun run dev
```

**Access the app:** http://localhost:5173

---

## 🎯 First Steps

### 1. Create an Account (Demo Mode)
1. Navigate to http://localhost:5173/signup
2. Enter any email (e.g., `officer@vendorbridge.com`)
3. Optional username
4. Create password: `Test@123` (meets requirements)
5. Confirm password
6. Select role: **Procurement Officer**
7. Click "Create account"
8. Auto-redirect to login

### 2. Login
1. Navigate to http://localhost:5173/login
2. Email: `officer@vendorbridge.com`
3. Password: `Test@123`
4. Click "Sign in"
5. **If 2FA enabled:** Check browser console for OTP code
6. Redirected to dashboard

### 3. Explore Features
- **Dashboard**: View analytics and quick actions
- **Vendors**: Add/manage vendors
- **RFQs**: Create RFQ, assign vendors
- **Quotations**: View submitted quotes
- **Compare**: Go to RFQ detail → Compare Quotations ⭐
- **Approvals**: Approve/reject requests
- **Invoices**: Generate and download PDF

---

## 📂 Project Structure (Simplified)

```
src/
├── routes/              # Pages (file-based routing)
│   ├── dashboard.tsx    # Main dashboard
│   ├── vendors/         # Vendor management
│   ├── rfq/             # RFQ management
│   └── ...
├── components/          # Reusable UI components
├── data/mockData.ts     # All mock data
├── lib/auth/            # Authentication library
└── context/AuthContext.tsx  # Auth state
```

---

## 🛠️ Common Commands

```bash
# Development
bun run dev              # Start dev server (HMR enabled)

# Building
bun run build            # Production build
bun run preview          # Preview production build

# Code Quality
bun run lint             # Run ESLint
bun run format           # Format with Prettier
tsc --noEmit             # Type check without output

# Dependencies
bun install              # Install all dependencies
bun update               # Update dependencies
```

---

## 🔑 Authentication Flow

### Login Flow
```
1. User enters email + password
2. authService.login() called
3. If 2FA enabled → Redirect to /verify-otp
4. If 2FA disabled → Store tokens, redirect to /dashboard
```

### Token Management
- **Access Token**: In-memory, 15 min TTL (lost on refresh)
- **Refresh Token**: localStorage, 7 days TTL (rotated)
- **Auto-refresh**: Triggered on 401 response

### Demo Mode
- All auth operations work without backend
- Users stored in localStorage
- OTP codes logged to console
- Email sending simulated

---

## 📊 Mock Data

**Location:** `src/data/mockData.ts`

**Collections:**
- `mockRFQs` - 5 RFQs with varying statuses
- `mockVendors` - 10+ vendors with categories
- `mockQuotations` - 9 quotations (3 per major RFQ)
- `mockApprovals` - 4 approval requests
- `mockPOs` - 4 purchase orders
- `mockInvoices` - 4 invoices
- `mockLogs` - 10 activity log entries

**Usage:**
```tsx
import { mockRFQs } from '@/data/mockData';

function RFQList() {
  const rfqs = mockRFQs.filter(r => r.status === 'Open');
  return <div>{/* Render */}</div>;
}
```

---

## 🎨 UI Components

### Using Existing Components

```tsx
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/Badge';

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Content here</p>
    <Badge variant="success">Active</Badge>
    <Button onClick={handleClick}>Action</Button>
  </CardContent>
</Card>
```

### Common Patterns

**Loading State:**
```tsx
{isLoading && <Loader2 className="animate-spin" />}
```

**Error State:**
```tsx
{error && <p className="text-red-600">{error.message}</p>}
```

**Empty State:**
```tsx
{items.length === 0 && <p className="text-gray-500">No items found</p>}
```

---

## 🔐 Protected Routes

All routes except `/login`, `/signup`, `/forgot-password`, `/reset-password` are protected.

**AuthGuard in `__root.tsx`:**
```tsx
// Checks for access token
// If missing → redirect to /login
// If expired → attempt refresh
// If refresh fails → logout
```

**Role-Based Rendering:**
```tsx
const { user } = useAuth();

{user.role === 'procurement_officer' && (
  <Button>Create RFQ</Button>
)}

{['manager', 'admin'].includes(user.role) && (
  <Link to="/approvals">Approvals</Link>
)}
```

---

## 📝 Forms (React Hook Form + Zod)

### Basic Form Pattern

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(2),
  email: z.string().email()
});

type FormData = z.infer<typeof schema>;

function MyForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema)
  });
  
  const onSubmit = (data: FormData) => {
    console.log(data);
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} />
      {errors.name && <p>{errors.name.message}</p>}
      <button type="submit">Submit</button>
    </form>
  );
}
```

---

## 🎯 Key Features to Demo

### 1. Quotation Comparison ⭐ (Most Impressive)
**Path:** `/rfq/RFQ-2026-002/compare`

**Features:**
- Side-by-side table
- Lowest price highlighted (green)
- Fastest delivery highlighted (blue)
- Top-rated vendor highlighted (amber)
- Sort by: Price, Delivery, Rating, Vendor
- Filter by: Rating (All, 4.0+, 4.5+)

### 2. Complete Workflow
```
1. Create RFQ → /rfq/create
2. Assign vendors → Select from list
3. Vendors submit quotes → /quotations/submit/:rfqId
4. Compare quotes → /rfq/:id/compare
5. Request approval → /approvals
6. Manager approves → Approval workflow
7. Generate PO → Auto from approval
8. Create invoice → /invoices/:id
9. Download PDF → window.print()
10. Activity logged → /activity-logs
```

### 3. Authentication
- Signup with password strength meter
- Login with 2FA
- Enable 2FA in profile
- Password reset flow

---

## 🐛 Troubleshooting

### Issue: "Module not found"
**Solution:** Run `bun install` again

### Issue: TypeScript errors
**Solution:** Check `tsconfig.json`, restart TS server in IDE

### Issue: Port 5173 already in use
**Solution:** Kill process or change port in `vite.config.ts`

### Issue: Hot reload not working
**Solution:** Restart dev server, check file watcher limits

### Issue: Can't see OTP code (2FA)
**Solution:** Open browser console (F12), look for "OTP code: XXXXXX"

---

## 📚 Documentation

- **README.md** - Project overview
- **FRONTEND_IMPLEMENTATION_PLAN.md** - Complete technical guide (38 pages)
- **AUTH_IMPLEMENTATION.md** - Auth system details
- **COMPLIANCE_ANALYSIS.md** - Hackathon compliance
- **FRONTEND_SUMMARY.md** - Executive summary
- **DEVELOPER_QUICK_START.md** - This guide

---

## 🤝 Need Help?

1. Check documentation files above
2. Search codebase for examples
3. Check component comments (JSDoc)
4. Look at similar existing components
5. Review `mockData.ts` for data structure

---

## ✅ Pre-Demo Checklist

- [ ] `bun run dev` works without errors
- [ ] Can signup and login
- [ ] Dashboard loads with data
- [ ] Can create RFQ
- [ ] Can compare quotations
- [ ] Can approve requests
- [ ] Can generate invoice PDF
- [ ] No console errors
- [ ] Browser devtools closed
- [ ] Full screen mode
- [ ] Good internet connection (if integrating backend)

---

## 🎓 Pro Tips

1. **Use TypeScript autocomplete** - Press Ctrl+Space for suggestions
2. **Component examples** - Check existing pages for patterns
3. **Styling** - Use Tailwind classes, check existing components
4. **Icons** - Import from `lucide-react`
5. **Forms** - Copy form pattern from existing forms
6. **Navigation** - Use `useNavigate()` from TanStack Router
7. **Auth** - Use `useAuth()` hook for user data
8. **Mock data** - Add to `mockData.ts` for new features

---

**Ready to code! Happy hacking! 🚀**
