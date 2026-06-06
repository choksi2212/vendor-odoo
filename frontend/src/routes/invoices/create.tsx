import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router";
import { useState } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { Button } from "@/components/Button";
import { inputCls } from "@/components/AuthShell";
import { invoiceAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/invoices/create")({
  component: InvoiceCreatePage,
  validateSearch: (search: Record<string, unknown>) => ({
    po: (search.po as string) || "",
  }),
});

function InvoiceCreatePage() {
  const { po } = Route.useSearch();
  const nav = useNavigate();
  const [notes, setNotes] = useState("Net 30 days. Bank transfer preferred.");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!po) {
      setError("No Purchase Order ID provided. Navigate from a PO detail page.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      await invoiceAPI.create(po, notes);
      nav({ to: "/invoices" });
    } catch (err: any) {
      setError(err.message || "Failed to create invoice");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <PageHeader title="Generate Invoice" breadcrumb={[{ label: "Invoices", to: "/invoices" }, { label: "Create" }]} />
      <form onSubmit={handleSubmit} className="max-w-xl rounded-lg border border-border bg-card p-6 space-y-4">
        {error && <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800">{error}</div>}
        
        <div>
          <label className="block text-xs font-medium mb-1">Purchase Order ID</label>
          <input className={inputCls} value={po} readOnly disabled />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Notes / Payment Terms</label>
          <textarea className={inputCls + " h-24"} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Payment terms, bank details, etc." />
        </div>
        <div className="flex gap-3 pt-2">
          <Button type="submit" disabled={isLoading}>
            {isLoading && <Loader2 size={16} className="animate-spin mr-1" />}
            {isLoading ? "Generating..." : "Generate Invoice"}
          </Button>
          <Button type="button" variant="ghost" onClick={() => nav({ to: "/invoices" })}>Cancel</Button>
        </div>
      </form>
    </Layout>
  );
}
