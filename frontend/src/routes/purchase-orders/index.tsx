import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { StatusBadge } from "@/components/Badge";
import { LinkButton } from "@/components/Button";
import { purchaseOrderAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/purchase-orders/")({ component: POListPage });

function POListPage() {
  const [pos, setPOs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => { loadPOs(); }, []);

  const loadPOs = async () => {
    setIsLoading(true);
    try {
      const data = await purchaseOrderAPI.list();
      setPOs(data.items || []);
    } catch (err) {
      console.error("Failed to load POs:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatAmount = (amt: any) => amt ? `Rs. ${Number(amt).toLocaleString("en-IN")}` : "-";

  if (isLoading) {
    return (
      <Layout>
        <PageHeader title="Purchase Orders" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Purchase Orders" }]} />
        <div className="flex items-center justify-center min-h-[300px]"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div>
      </Layout>
    );
  }

  return (
    <Layout>
      <PageHeader title="Purchase Orders" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Purchase Orders" }]} />
      {pos.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">No purchase orders found.</div>
      ) : (
        <DataTable columns={["PO Number", "Vendor", "Total Amount", "Status", "Date", "Actions"]}>
          {pos.map((po) => (
            <Tr key={po.id}>
              <Td className="font-mono font-medium">{po.poNumber}</Td>
              <Td>{po.vendorName || "-"}</Td>
              <Td className="font-mono">{formatAmount(po.totalAmount)}</Td>
              <Td><StatusBadge status={po.status} /></Td>
              <Td className="text-muted-foreground text-xs">{po.createdAt ? new Date(po.createdAt).toLocaleDateString() : "-"}</Td>
              <Td><LinkButton to={`/purchase-orders/${po.id}`} variant="ghost">View</LinkButton></Td>
            </Tr>
          ))}
        </DataTable>
      )}
    </Layout>
  );
}
