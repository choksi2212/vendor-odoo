import { Link, useLocation } from "@tanstack/react-router";
import { useAuth, type Role } from "@/context/AuthContext";

type NavItem = { label: string; to: string };

const navByRole: Record<Role, NavItem[]> = {
  "Procurement Officer": [
    { label: "Dashboard", to: "/dashboard" },
    { label: "Vendors", to: "/vendors" },
    { label: "RFQs", to: "/rfq" },
    { label: "Quotation Comparison", to: "/rfq" },
    { label: "Approvals", to: "/approvals" },
    { label: "Purchase Orders", to: "/purchase-orders" },
    { label: "Invoices", to: "/invoices" },
    { label: "Activity Logs", to: "/activity-logs" },
    { label: "Reports", to: "/reports" },
  ],
  Vendor: [
    { label: "Dashboard", to: "/dashboard" },
    { label: "RFQs", to: "/rfq" },
    { label: "My Quotations", to: "/quotations" },
    { label: "Activity Logs", to: "/activity-logs" },
  ],
  "Manager / Approver": [
    { label: "Dashboard", to: "/dashboard" },
    { label: "Approvals", to: "/approvals" },
    { label: "Purchase Orders", to: "/purchase-orders" },
    { label: "Invoices", to: "/invoices" },
    { label: "Reports", to: "/reports" },
  ],
  Admin: [
    { label: "Dashboard", to: "/dashboard" },
    { label: "Vendors", to: "/vendors" },
    { label: "RFQs", to: "/rfq" },
    { label: "Approvals", to: "/approvals" },
    { label: "Purchase Orders", to: "/purchase-orders" },
    { label: "Invoices", to: "/invoices" },
    { label: "Activity Logs", to: "/activity-logs" },
    { label: "Reports", to: "/reports" },
    { label: "Settings", to: "/settings" },
  ],
};

const icons: Record<string, string> = {
  Dashboard: "▦", Vendors: "◫", RFQs: "≡", "Quotation Comparison": "⇄", Approvals: "✓",
  "Purchase Orders": "◰", Invoices: "₹", "Activity Logs": "◷", Reports: "◧",
  Settings: "⚙", "My Quotations": "✎",
};

export function Sidebar() {
  const { role, name } = useAuth();
  const loc = useLocation();
  const items = navByRole[role];

  return (
    <aside className="fixed left-0 top-0 z-30 flex h-screen w-60 flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-16 items-center gap-2.5 border-b border-sidebar-border px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[color:var(--action)] font-display text-base font-bold text-[color:var(--action-foreground)]">V</div>
        <div className="font-display text-lg font-semibold tracking-tight">VendorBridge</div>
      </div>
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">Workspace</p>
        <ul className="space-y-0.5">
          {items.map((it) => {
            const active = loc.pathname === it.to || (it.to !== "/dashboard" && loc.pathname.startsWith(it.to));
            return (
              <li key={it.label}>
                <Link
                  to={it.to}
                  className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                    active ? "bg-sidebar-accent text-white" : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-white"
                  }`}
                >
                  <span className="w-4 text-center text-sidebar-foreground/60">{icons[it.label] ?? "•"}</span>
                  <span>{it.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-sidebar-accent text-sm font-semibold">
            {name.split(" ").map((p) => p[0]).slice(0, 2).join("")}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-white">{name}</p>
            <p className="truncate text-[11px] text-sidebar-foreground/60">{role}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
