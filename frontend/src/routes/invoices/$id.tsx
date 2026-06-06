import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { StatusBadge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { invoiceAPI } from "@/lib/api/endpoints";
import { Loader2, Download, Mail, CheckCircle } from "lucide-react";

export const Route = createFileRoute("/invoices/$id")({ component: InvoiceDetailPage });

function InvoiceDetailPage() {
  const { id } = Route.useParams();
  const [invoice, setInvoice] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    invoiceAPI.getById(id).then(setInvoice).catch(console.error).finally(() => setIsLoading(false));
  }, [id]);

  const handleDownloadPDF = async () => {
    try {
      const blob = await invoiceAPI.downloadPDF(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${invoice.invoiceNumber}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message || "Failed to download PDF");
    }
  };

  const handleIssue = async () => {
    try {
      const updated = await invoiceAPI.issue(id);
      setInvoice(updated);
    } catch (err: any) {
      alert(err.message || "Failed to issue invoice");
    }
  };

  const handleMarkPaid = async () => {
    try {
      const updated = await invoiceAPI.markPaid(id);
      setInvoice(updated);
    } catch (err: any) {
      alert(err.message || "Failed to mark as paid");
    }
  };

  const formatAmount = (amt: any) => amt ? `Rs. ${Number(amt).toLocaleString("en-IN")}` : "-";

  if (isLoading) {
    return <Layout><div className="flex items-center justify-center min-h-[300px]"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div></Layout>;
  }
  if (!invoice) {
    return <Layout><div className="p-8 text-center text-muted-foreground">Invoice not found.</div></Layout>;
  }

  return (
    <Layout>
      <PageHeader title={`Invoice: ${invoice.invoiceNumber}`} breadcrumb={[{ label: "Invoices", to: "/invoices" }, { label: invoice.invoiceNumber }]}
        actions={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={handleDownloadPDF}><Download size={16} className="mr-1" /> PDF</Button>
            {invoice.status === "draft" && <Button onClick={handleIssue}>Issue Invoice</Button>}
            {invoice.status === "issued" && <Button onClick={handleMarkPaid}><CheckCircle size={16} className="mr-1" /> Mark Paid</Button>}
          </div>
        }
      />

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="font-display text-sm font-semibold mb-4">Invoice Details</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-muted-foreground">Invoice #</dt><dd className="font-mono font-medium">{invoice.invoiceNumber}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">PO Ref</dt><dd className="font-mono">{invoice.poNumber || "-"}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Status</dt><dd><StatusBadge status={invoice.status} /></dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Vendor</dt><dd>{invoice.vendorName || "-"}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Date</dt><dd>{invoice.createdAt ? new Date(invoice.createdAt).toLocaleDateString() : "-"}</dd></div>
            {invoice.paidAt && <div className="flex justify-between"><dt className="text-muted-foreground">Paid At</dt><dd className="text-green-600">{new Date(invoice.paidAt).toLocaleDateString()}</dd></div>}
          </dl>
        </div>
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="font-display text-sm font-semibold mb-4">Amount Breakdown</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-muted-foreground">Subtotal</dt><dd className="font-mono">{formatAmount(invoice.subtotal)}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">GST ({invoice.taxRate}%)</dt><dd className="font-mono">{formatAmount(invoice.taxAmount)}</dd></div>
            <div className="flex justify-between border-t pt-2"><dt className="font-semibold">Grand Total</dt><dd className="font-mono font-bold text-lg">{formatAmount(invoice.totalAmount)}</dd></div>
          </dl>
        </div>
      </div>

      <div className="mt-6 rounded-lg border border-border bg-card p-6">
        <h3 className="font-display text-sm font-semibold mb-4">Line Items</h3>
        <table className="w-full text-sm">
          <thead><tr className="border-b text-left text-muted-foreground"><th className="pb-2">Product</th><th className="pb-2">Qty</th><th className="pb-2">Unit</th><th className="pb-2 text-right">Unit Price</th><th className="pb-2 text-right">Total</th></tr></thead>
          <tbody>
            {(invoice.lineItems || []).map((li: any, i: number) => (
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

      {invoice.notes && (
        <div className="mt-6 rounded-lg border border-border bg-card p-6">
          <h3 className="font-display text-sm font-semibold mb-2">Notes / Payment Terms</h3>
          <p className="text-sm text-muted-foreground">{invoice.notes}</p>
        </div>
      )}
    </Layout>
  );
}
