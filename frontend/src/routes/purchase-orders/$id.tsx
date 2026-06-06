import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { StatusBadge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { purchaseOrderAPI, invoiceAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/purchase-orders/$id")({ component: PODetailPage });

function PODetailPage() {
  const { id } = Route.useParams();
  const nav = useNavigate();
  const [po, setPO] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    purchaseOrderAPI.getById(id).then(setPO).catch(console.error).finally(() => setIsLoading(false));
  }, [id]);

  const handleGenerateInvoice = async () => {
    try {
      await invoiceAPI.create(po.id, "Net 30 days");
      alert("Invoice generated successfully!");
      nav({ to: "/invoices" });
    } catch (err: any) {
      alert(err.message || "Failed to generate invoice");
    }
  };

  const formatAmount = (amt: any) => amt ? `Rs. ${Number(amt).toLocaleString("en-IN")}` : "-";

  if (isLoading) {
    return <Layout><div className="flex items-center justify-center min-h-[300px]"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div></Layout>;
  }
  if (!po) {
    return <Layout><div className="p-8 text-center text-muted-foreground">Purchase Order not found.</div></Layout>;
  }

  return (
    <Layout>
      <PageHeader title={`Purchase Order: ${po.poNumber}`} breadcrumb={[{ label: "Purchase Orders", to: "/purchase-orders" }, { label: po.poNumber }]}
        actions={po.status === "issued" && <Button onClick={handleGenerateInvoice}>Generate Invoice</Button>}
      />
      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="font-display text-sm font-semibold mb-4">PO Details</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-muted-foreground">PO Number</dt><dd className="font-mono font-medium">{po.poNumber}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Status</dt><dd><StatusBadge status={po.status} /></dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Vendor</dt><dd>{po.vendorName || "-"}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Created</dt><dd>{po.createdAt ? new Date(po.createdAt).toLocaleDateString() : "-"}</dd></div>
          </dl>
        </div>
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="font-display text-sm font-semibold mb-4">Amount Breakdown</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-muted-foreground">Subtotal</dt><dd className="font-mono">{formatAmount(po.subtotal)}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">GST ({po.taxRate}%)</dt><dd className="font-mono">{formatAmount(po.taxAmount)}</dd></div>
            <div className="flex justify-between border-t pt-2"><dt className="font-semibold">Grand Total</dt><dd className="font-mono font-bold text-lg">{formatAmount(po.totalAmount)}</dd></div>
          </dl>
        </div>
      </div>

      <div className="mt-6 rounded-lg border border-border bg-card p-6">
        <h3 className="font-display text-sm font-semibold mb-4">Line Items</h3>
        <table className="w-full text-sm">
          <thead><tr className="border-b text-left text-muted-foreground"><th className="pb-2">Product</th><th className="pb-2">Qty</th><th className="pb-2">Unit</th><th className="pb-2 text-right">Unit Price</th><th className="pb-2 text-right">Total</th></tr></thead>
          <tbody>
            {(po.lineItems || []).map((li: any, i: number) => (
              <tr key={i} className="border-b last:border-0">
                <td className="py-2 font-medium">{li.productName}</td>
                <td className="py-2">{li.quantity}</td>
                <td className="py-2">{li.unit}</td>
                <td className="py-2 text-right font-mono">{formatAmount(li.unitPrice)}</td>
                <td className="py-2 text-right font-mono">{formatAmount(li.totalPrice)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
