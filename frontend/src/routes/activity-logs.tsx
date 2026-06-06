import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { activityLogAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/activity-logs")({ component: ActivityLogsPage });

function ActivityLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => { loadLogs(); }, [filter]);

  const loadLogs = async () => {
    setIsLoading(true);
    try {
      const data = await activityLogAPI.list({
        entityType: filter || undefined,
      });
      setLogs(data.items || []);
    } catch (err) {
      console.error("Failed to load activity logs:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <PageHeader title="Activity Logs" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Activity Logs" }]} />

      <div className="mb-4 flex gap-2">
        {["", "VENDOR", "RFQ", "QUOTATION", "APPROVAL", "PURCHASE_ORDER", "INVOICE"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${filter === f ? "bg-[color:var(--action)] text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}
          >
            {f || "All"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[200px]"><Loader2 className="animate-spin h-6 w-6 text-gray-400" /></div>
      ) : logs.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">No activity logs found.</div>
      ) : (
        <DataTable columns={["Timestamp", "Action", "Entity", "Details"]}>
          {logs.map((log) => (
            <Tr key={log.id}>
              <Td className="text-xs text-muted-foreground whitespace-nowrap">{log.createdAt ? new Date(log.createdAt).toLocaleString() : "-"}</Td>
              <Td><span className="rounded bg-muted px-2 py-0.5 text-xs font-medium">{log.action}</span></Td>
              <Td><span className="text-xs">{log.entityType}</span>{log.entityId && <span className="ml-1 text-xs text-muted-foreground font-mono">{log.entityId.slice(0, 8)}...</span>}</Td>
              <Td className="text-xs text-muted-foreground max-w-[300px] truncate">{log.details ? JSON.stringify(log.details).slice(0, 80) : "-"}</Td>
            </Tr>
          ))}
        </DataTable>
      )}
    </Layout>
  );
}
