import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { StatCard } from "@/components/StatCard";
import { DataTable, Td, Tr } from "@/components/Table";
import { StatusBadge } from "@/components/Badge";
import { Button, LinkButton } from "@/components/Button";
import { useAuth } from "@/context/AuthContext";
import { analyticsAPI, rfqAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/dashboard")({ component: Dashboard });

function Dashboard() {
  const { role, name, user } = useAuth();
  const nav = useNavigate();
  const isVendor = role === "Vendor";
  
  const [stats, setStats] = useState<any>(null);
  const [recentRFQs, setRecentRFQs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Fetch dashboard stats (skip for vendors as they don't have access)
        if (!isVendor) {
          const dashboardData = await analyticsAPI.getDashboard();
          setStats(dashboardData);
        } else {
          // Set empty stats for vendors
          setStats({
            pendingApprovals: 0,
            activeRfqs: 0,
            totalPosThisMonth: 0,
            totalInvoicesThisMonth: 0,
            totalSpendThisMonth: 0,
            totalQuotations: 0,
            outstandingInvoices: 0,
          });
        }
        
        // Fetch recent RFQs (all roles can access)
        const rfqData = await rfqAPI.list({ page: 1 });
        setRecentRFQs(rfqData.items?.slice(0, 5) || []);
      } catch (err: any) {
        console.error('Dashboard load error:', err);
        setError(err.message || 'Failed to load dashboard');
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      loadDashboard();
    }
  }, [user, isVendor]);

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="animate-spin h-8 w-8 text-gray-400" />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="rounded-md bg-red-50 border border-red-200 p-4">
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 text-sm text-red-600 hover:underline"
          >
            Retry
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <PageHeader
        title={`Good morning, ${name.split(" ")[0]}`}
        breadcrumb={[{ label: "Workspace" }, { label: "Dashboard" }]}
        actions={!isVendor && (
          <>
            <Button variant="secondary" onClick={() => nav({ to: "/vendors/add" })}>+ Add Vendor</Button>
            <Button onClick={() => nav({ to: "/rfq/create" })}>+ Create RFQ</Button>
          </>
        )}
      />

      {isVendor ? (
        // Vendor Dashboard View
        <>
          <div className="mb-6 rounded-lg border border-info/30 bg-info/5 p-4">
            <h3 className="font-semibold text-info-foreground">Vendor Portal</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              View RFQs assigned to you and submit quotations
            </p>
          </div>
          
          <div className="mt-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-display text-base font-semibold">RFQs Assigned to You</h2>
              <LinkButton to="/rfq" variant="ghost">View all →</LinkButton>
            </div>
            {recentRFQs.length > 0 ? (
              <DataTable columns={["RFQ / Reference", "Status", "Deadline", "Action"]}>
                {recentRFQs.map((r) => (
                  <Tr key={r.id}>
                    <Td>
                      <div className="font-medium">{r.title}</div>
                      <div className="text-xs text-muted-foreground">{r.productName}</div>
                    </Td>
                    <Td><StatusBadge status={r.status} /></Td>
                    <Td className="text-muted-foreground">{r.deadline}</Td>
                    <Td><LinkButton to={`/rfq/${r.id}`} variant="ghost">View & Quote →</LinkButton></Td>
                  </Tr>
                ))}
              </DataTable>
            ) : (
              <div className="rounded-lg border border-border bg-card p-8 text-center text-sm text-muted-foreground">
                No RFQs assigned to you yet
              </div>
            )}
          </div>
        </>
      ) : (
        // Procurement Officer / Manager / Admin Dashboard View
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard 
              label="Pending Approvals" 
              value={stats?.pendingApprovals || 0} 
              hint="Awaiting manager action" 
              accent="warning" 
            />
            <StatCard 
              label="Active RFQs" 
              value={stats?.activeRfqs || 0} 
              hint="Currently soliciting quotes" 
              accent="info" 
            />
            <StatCard 
              label="Recent POs" 
              value={stats?.totalPosThisMonth || 0} 
              hint="Issued in last 30 days" 
              accent="primary" 
            />
            <StatCard 
              label="Recent Invoices" 
              value={stats?.totalInvoicesThisMonth || 0} 
              hint={stats?.totalSpendThisMonth ? `₹${(stats.totalSpendThisMonth / 100000).toFixed(1)}L total` : 'No data'} 
              accent="success" 
            />
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-display text-base font-semibold">Recent Activity</h2>
                <LinkButton to="/activity-logs" variant="ghost">View all →</LinkButton>
              </div>
              {recentRFQs.length > 0 ? (
                <DataTable columns={["RFQ / Reference", "Status", "Date", "Action"]}>
                  {recentRFQs.map((r) => (
                    <Tr key={r.id}>
                      <Td>
                        <div className="font-medium">{r.title}</div>
                        <div className="text-xs text-muted-foreground">{r.id}</div>
                      </Td>
                      <Td><StatusBadge status={r.status} /></Td>
                      <Td className="text-muted-foreground">{r.deadline}</Td>
                      <Td><LinkButton to={`/rfq/${r.id}`} variant="ghost">Open →</LinkButton></Td>
                    </Tr>
                  ))}
                </DataTable>
              ) : (
                <div className="rounded-lg border border-border bg-card p-8 text-center text-sm text-muted-foreground">
                  No recent activity
                </div>
              )}
            </div>
            <div className="rounded-lg border border-border bg-card p-5">
              <h2 className="font-display text-base font-semibold">Workflow Snapshot</h2>
              <p className="mt-1 text-xs text-muted-foreground">RFQ → Quotation → PO → Invoice</p>
              <ol className="mt-5 space-y-3 text-sm">
                {[
                  { k: "RFQs Open", v: stats?.activeRfqs || 0, c: "info" },
                  { k: "Quotations Received", v: stats?.totalQuotations || 0, c: "primary" },
                  { k: "Approvals Pending", v: stats?.pendingApprovals || 0, c: "warning" },
                  { k: "POs Issued", v: stats?.totalPosThisMonth || 0, c: "success" },
                  { k: "Invoices Outstanding", v: stats?.outstandingInvoices || 0, c: "primary" },
                ].map((row) => (
                  <li key={row.k} className="flex items-center justify-between border-b border-border/60 pb-2 last:border-0">
                    <span className="text-muted-foreground">{row.k}</span>
                    <span className="font-display text-lg font-semibold">{row.v}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}
