import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { StatusBadge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { approvalAPI } from "@/lib/api/endpoints";
import { useAuth } from "@/context/AuthContext";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/approvals")({ component: ApprovalsPage });

function ApprovalsPage() {
  const { role } = useAuth();
  const isManager = role === "Manager / Approver" || role === "Admin";
  const [rows, setRows] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [rejecting, setRejecting] = useState<string | null>(null);
  const [remarks, setRemarks] = useState("");

  useEffect(() => { loadApprovals(); }, []);

  const loadApprovals = async () => {
    setIsLoading(true);
    try {
      const data = await approvalAPI.list();
      setRows(data.items || []);
    } catch (err) {
      console.error("Failed to load approvals:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await approvalAPI.approve(id, "Approved");
      await loadApprovals();
    } catch (err: any) {
      alert(err.message || "Failed to approve");
    }
  };

  const handleReject = async (id: string) => {
    try {
      await approvalAPI.reject(id, remarks || "Rejected");
      setRejecting(null);
      setRemarks("");
      await loadApprovals();
    } catch (err: any) {
      alert(err.message || "Failed to reject");
    }
  };

  const formatAmount = (amt: any) => {
    if (!amt) return "-";
    return `Rs. ${Number(amt).toLocaleString("en-IN")}`;
  };

  if (isLoading) {
    return (
      <Layout>
        <PageHeader title="Approval Workflow" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Approvals" }]} />
        <div className="flex items-center justify-center min-h-[300px]"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div>
      </Layout>
    );
  }

  return (
    <Layout>
      <PageHeader title="Approval Workflow" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Approvals" }]} />

      {rows.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">
          No approval requests found.
        </div>
      ) : (
        <DataTable columns={["RFQ", "Vendor", "Amount", "Requested By", "Status", ...(isManager ? ["Actions"] : [])]}>
          {rows.map((a) => (
            <Tr key={a.id}>
              <Td><div className="font-medium">{a.rfqTitle || "-"}</div></Td>
              <Td>{a.vendorName || "-"}</Td>
              <Td className="font-mono">{formatAmount(a.totalAmount)}</Td>
              <Td>{a.requestedByName || "-"}</Td>
              <Td><StatusBadge status={a.status} /></Td>
              {isManager && (
                <Td>
                  {a.status === "pending" ? (
                    <div className="flex gap-2">
                      <Button onClick={() => handleApprove(a.id)}>Approve</Button>
                      {rejecting === a.id ? (
                        <div className="flex gap-1">
                          <input
                            value={remarks}
                            onChange={(e) => setRemarks(e.target.value)}
                            placeholder="Reason..."
                            className="rounded border border-border px-2 py-1 text-xs w-32"
                          />
                          <Button variant="ghost" onClick={() => handleReject(a.id)}>Confirm</Button>
                        </div>
                      ) : (
                        <Button variant="ghost" onClick={() => setRejecting(a.id)}>Reject</Button>
                      )}
                    </div>
                  ) : (
                    <span className="text-xs text-muted-foreground">{a.remarks || "-"}</span>
                  )}
                    <span className="text-xs text-muted-foreground">{a.remarks || "-"}</span>
                  )}
                </Td>
              )}
            </Tr>
          ))}
        </DataTable>
      )}
    </Layout>
  );
}
