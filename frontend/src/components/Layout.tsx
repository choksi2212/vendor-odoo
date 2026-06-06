import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import { type ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { useAuth } from "@/context/AuthContext";
import { Badge } from "./Badge";

export function PageHeader({ title, breadcrumb, actions }: { title: string; breadcrumb?: { label: string; to?: string }[]; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b border-border pb-5">
      <div>
        {breadcrumb && breadcrumb.length > 0 && (
          <nav className="mb-1.5 flex items-center gap-1.5 text-xs text-muted-foreground">
            {breadcrumb.map((b, i) => (
              <span key={i} className="flex items-center gap-1.5">
                {b.to ? <Link to={b.to} className="hover:text-foreground">{b.label}</Link> : <span>{b.label}</span>}
                {i < breadcrumb.length - 1 && <span>/</span>}
              </span>
            ))}
          </nav>
        )}
        <h1 className="font-display text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

function Topbar() {
  const { role, name, setRole } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const titleMap: Record<string, string> = {
    "/dashboard": "Dashboard", "/vendors": "Vendor Management", "/rfq": "Request for Quotations",
    "/approvals": "Approval Workflow", "/purchase-orders": "Purchase Orders", "/invoices": "Invoices",
    "/activity-logs": "Activity Logs", "/reports": "Reports & Analytics", "/settings": "Admin Settings",
    "/quotations": "My Quotations",
  };
  const pageTitle = Object.entries(titleMap).find(([k]) => loc.pathname.startsWith(k))?.[1] ?? "VendorBridge";

  return (
    <header className="fixed left-60 right-0 top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/95 px-8 backdrop-blur">
      <div className="flex items-center gap-3">
        <p className="text-sm text-muted-foreground">{pageTitle}</p>
      </div>
      <div className="flex items-center gap-4">
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as typeof role)}
          className="rounded-md border border-border bg-background px-2.5 py-1.5 text-xs font-medium text-foreground"
        >
          <option>Procurement Officer</option>
          <option>Vendor</option>
          <option>Manager / Approver</option>
          <option>Admin</option>
        </select>
        <Badge variant="info">{role}</Badge>
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
            {name.split(" ").map((p) => p[0]).slice(0, 2).join("")}
          </div>
          <span className="text-sm font-medium text-foreground">{name}</span>
        </div>
        <button
          onClick={() => nav({ to: "/login" })}
          className="rounded-md border border-border bg-background px-2.5 py-1.5 text-xs font-medium hover:bg-accent"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <Topbar />
      <main className="ml-60 pt-16">
        <div className="mx-auto max-w-[1400px] px-8 py-8">{children}</div>
      </main>
    </div>
  );
}
