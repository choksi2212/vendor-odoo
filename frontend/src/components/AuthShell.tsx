import { Link } from "@tanstack/react-router";
import { type ReactNode } from "react";

export const inputCls = "w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-[color:var(--action)] focus:outline-none focus:ring-2 focus:ring-[color:var(--action)]/20";

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-foreground">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-[11px] text-muted-foreground">{hint}</span>}
    </label>
  );
}

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-muted/40">
      <div className="mx-auto flex min-h-screen max-w-6xl items-stretch px-6 py-10">
        <div className="hidden flex-1 flex-col justify-between rounded-l-2xl bg-sidebar p-12 text-sidebar-foreground lg:flex">
          <div>
            <Link to="/login" className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[color:var(--action)] font-display text-base font-bold text-[color:var(--action-foreground)]">V</div>
              <span className="font-display text-xl font-semibold">VendorBridge</span>
            </Link>
            <h2 className="mt-16 font-display text-3xl font-semibold leading-tight">Procurement, end to end.</h2>
            <p className="mt-4 max-w-md text-sm text-sidebar-foreground/70">
              Digitize RFQs, vendor quotations, side-by-side comparisons, approvals, purchase orders and invoices — all on a single role-gated workspace.
            </p>
          </div>
          <div className="space-y-3 text-xs text-sidebar-foreground/60">
            {["RFQ → Quotation → PO → Invoice", "Role-based access for 4 personas", "PDF + Email invoice dispatch", "Full audit trail and analytics"].map((t) => (
              <div key={t} className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--action)]" />
                {t}
              </div>
            ))}
          </div>
        </div>
        <div className="flex flex-1 items-center justify-center rounded-2xl border border-border bg-card lg:rounded-l-none lg:rounded-r-2xl lg:border-l-0">
          <div className="w-full max-w-md px-8 py-12">{children}</div>
        </div>
      </div>
    </div>
  );
}
