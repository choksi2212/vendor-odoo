import { type ReactNode } from "react";

export function StatCard({ label, value, hint, accent }: { label: string; value: ReactNode; hint?: string; accent?: "primary" | "success" | "warning" | "info" }) {
  const accentBar: Record<string, string> = {
    primary: "bg-[color:var(--action)]",
    success: "bg-[color:var(--success)]",
    warning: "bg-[color:var(--warning)]",
    info: "bg-[color:var(--info)]",
  };
  return (
    <div className="relative overflow-hidden rounded-lg border border-border bg-card p-5">
      <div className={`absolute left-0 top-0 h-full w-1 ${accentBar[accent ?? "primary"]}`} />
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-2 font-display text-3xl font-semibold text-foreground">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}
