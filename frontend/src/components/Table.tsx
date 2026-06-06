import { type ReactNode } from "react";

export function DataTable({ columns, children, empty }: { columns: string[]; children: ReactNode; empty?: boolean }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/60">
            <tr>
              {columns.map((c) => (
                <th key={c} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {empty ? (
              <tr><td colSpan={columns.length} className="px-4 py-10 text-center text-sm text-muted-foreground">No records found.</td></tr>
            ) : children}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-border bg-muted/30 px-4 py-2.5 text-xs text-muted-foreground">
        <span>Showing recent records</span>
        <div className="flex gap-2">
          <button className="rounded border border-border bg-background px-2.5 py-1 hover:bg-accent">Previous</button>
          <button className="rounded border border-border bg-background px-2.5 py-1 hover:bg-accent">Next</button>
        </div>
      </div>
    </div>
  );
}

export function Td({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <td className={`px-4 py-3 text-sm text-foreground ${className}`}>{children}</td>;
}

export function Tr({ children }: { children: ReactNode }) {
  return <tr className="hover:bg-muted/40 transition-colors">{children}</tr>;
}
