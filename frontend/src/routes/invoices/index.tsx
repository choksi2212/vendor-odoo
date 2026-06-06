import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { StatusBadge } from "@/components/Badge";
import { LinkButton } from "@/components/Button";
import { invoiceAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/invoices/")({ component: InvoicesPage });

function InvoicesPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => { loadInvoices(); }, []);

  const loadInvoices = async () => {
    setIsLoading(true);
    try {
      const data = await invoiceAPI.list();
      setInvoices(data.items || []);
    } catch (err) {
      console.error("Failed to load invoices:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatAmount = (amt: any) => amt ? `Rs. ${Number(amt).toLocaleString("en-IN")}` : "-";

  if (isLoading) {
    return (
      <Layout>
        <PageHeader title="Invoices" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Invoices" }]} />
        <div className="flex items-center justify-center min-h-[300px]"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div>
      </Layout>
    );
  }

  return (
    <Layout>
      <PageHeader title="Invoices" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Invoices" }]} />
      {invoices.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">No invoices found.</div>
      ) : (
        <DataTable columns={["Invoice #", "PO #", "Vendor", "Total", "Status", "Date", "Actions"]}>
          {invoices.map((inv) => (
            <Tr key={inv.id}>
              <Td className="font-mono font-medium">{inv.invoiceNumber}</Td>
              <Td className="font-mono text-xs">{inv.poNumber || "-"}</Td>
              <Td>{inv.vendorName || "-"}</Td>
              <Td className="font-mono">{formatAmount(inv.totalAmount)}</Td>
              <Td><StatusBadge status={inv.status} /></Td>
              <Td className="text-xs text-muted-foreground">{inv.createdAt ? new Date(inv.createdAt).toLocaleDateString() : "-"}</Td>
              <Td><LinkButton to={`/invoices/${inv.id}`} variant="ghost">View</LinkButton></Td>
            </Tr>
          ))}
        </DataTable>
      )}
    </Layout>
  );
}
