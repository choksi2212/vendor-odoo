import { type ReactNode } from "react";

type Variant = "success" | "warning" | "danger" | "info" | "neutral";

const styles: Record<Variant, string> = {
  success: "bg-[color:var(--success)]/15 text-[color:var(--success-foreground)] border-[color:var(--success)]/30",
  warning: "bg-[color:var(--warning)]/20 text-[color:var(--warning-foreground)] border-[color:var(--warning)]/40",
  danger: "bg-[color:var(--destructive)]/10 text-[color:var(--destructive)] border-[color:var(--destructive)]/30",
  info: "bg-[color:var(--info)]/15 text-[color:var(--info-foreground)] border-[color:var(--info)]/30",
  neutral: "bg-muted text-muted-foreground border-border",
};

export function Badge({ children, variant = "neutral" }: { children: ReactNode; variant?: Variant }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[variant]}`}>
      {children}
    </span>
  );
}

export function statusToVariant(status: string): Variant {
  const s = status.toLowerCase();
  if (["active", "approved", "paid", "issued", "submitted"].includes(s)) return "success";
  if (["pending", "open", "under review"].includes(s)) return "warning";
  if (["rejected", "inactive", "cancelled"].includes(s)) return "danger";
  if (["draft"].includes(s)) return "info";
  if (["closed"].includes(s)) return "neutral";
  return "neutral";
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge variant={statusToVariant(status)}>{status}</Badge>;
}
