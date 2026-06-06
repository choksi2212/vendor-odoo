import React, { type ButtonHTMLAttributes, type ReactNode } from "react";
import { Link } from "@tanstack/react-router";

type Variant = "primary" | "secondary" | "danger" | "ghost";

const base = "inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap";
const variants: Record<Variant, string> = {
  primary: "bg-[color:var(--action)] text-[color:var(--action-foreground)] hover:bg-[color:var(--action)]/90",
  secondary: "bg-background text-foreground border border-border hover:bg-accent",
  danger: "bg-[color:var(--destructive)] text-[color:var(--destructive-foreground)] hover:bg-[color:var(--destructive)]/90",
  ghost: "text-foreground hover:bg-accent",
};

export function Button({ variant = "primary", className = "", children, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; children: ReactNode }) {
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...rest}>
      {children}
    </button>
  );
}

export function LinkButton({ to, variant = "primary", children, params, search }: { to: string; variant?: Variant; children: ReactNode; params?: Record<string, string>; search?: Record<string, string> }) {
  const L = Link as unknown as React.ComponentType<{ to: string; params?: Record<string, string>; search?: Record<string, string>; className?: string; children?: ReactNode }>;
  return (
    <L to={to} params={params} search={search} className={`${base} ${variants[variant]}`}>{children}</L>
  );
}
