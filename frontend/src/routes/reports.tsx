import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { analyticsAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/reports")({ component: ReportsPage });

function ReportsPage() {
  const [spending, setSpending] = useState<any>(null);
  const [vendorPerf, setVendorPerf] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [sp, vp, tr] = await Promise.all([
          analyticsAPI.getSpending(),
          analyticsAPI.getVendorPerformance(),
          analyticsAPI.getMonthlyTrends(6),
        ]);
        setSpending(sp);
        setVendorPerf(vp);
        setTrends(tr);
      } catch (err) {
        console.error("Failed to load reports:", err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  const formatAmount = (amt: any) => amt ? `Rs. ${Number(amt).toLocaleString("en-IN")}` : "Rs. 0";

  if (isLoading) {
    return (
      <Layout>
        <PageHeader title="Reports & Analytics" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Reports" }]} />
        <div className="flex items-center justify-center min-h-[300px]"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div>
      </Layout>
    );
  }

  return (
    <Layout>
      <PageHeader title="Reports & Analytics" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Reports" }]} />

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-3 mb-8">
        <div className="rounded-lg border border-border bg-card p-6">
          <p className="text-xs text-muted-foreground">Total Spend</p>
          <p className="mt-1 text-2xl font-bold font-mono">{formatAmount(spending?.totalSpend)}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6">
          <p className="text-xs text-muted-foreground">Active Vendors</p>
          <p className="mt-1 text-2xl font-bold">{vendorPerf?.totalVendors || 0}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6">
          <p className="text-xs text-muted-foreground">Spending Breakdown</p>
          <p className="mt-1 text-2xl font-bold">{spending?.breakdown?.length || 0} vendors</p>
        </div>
      </div>

      {/* Monthly Trends */}
      {trends && trends.months && (
        <section className="mb-8">
          <h2 className="mb-3 font-display text-base font-semibold">Monthly Procurement Trends</h2>
          <div className="rounded-lg border border-border bg-card p-6">
            <div className="flex items-end gap-2 h-40">
              {trends.months.map((m: any) => {
                const maxSpend = Math.max(...trends.months.map((x: any) => Number(x.totalSpend) || 1));
                const height = maxSpend > 0 ? (Number(m.totalSpend) / maxSpend) * 100 : 0;
                return (
                  <div key={m.month} className="flex-1 flex flex-col items-center gap-1">
                    <div className="w-full bg-[color:var(--action)] rounded-t" style={{ height: `${Math.max(height, 2)}%` }} title={formatAmount(m.totalSpend)} />
                    <span className="text-[10px] text-muted-foreground">{m.month.split("-")[1]}</span>
                  </div>
                );
              })}
            </div>
            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              <span>{trends.months[0]?.month}</span>
              <span>{trends.months[trends.months.length - 1]?.month}</span>
            </div>
          </div>
        </section>
      )}

      {/* Vendor Performance */}
      {vendorPerf && vendorPerf.vendors && vendorPerf.vendors.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 font-display text-base font-semibold">Vendor Performance</h2>
          <DataTable columns={["Vendor", "RFQs Invited", "Submissions", "Rate", "Won", "Order Value"]}>
            {vendorPerf.vendors.map((v: any) => (
              <Tr key={v.vendorId}>
                <Td className="font-medium">{v.vendorName}</Td>
                <Td>{v.totalRfqsInvited}</Td>
                <Td>{v.quotationsSubmitted}</Td>
                <Td>{v.submissionRate}%</Td>
                <Td>{v.quotationsWon}</Td>
                <Td className="font-mono">{formatAmount(v.totalOrderValue)}</Td>
              </Tr>
            ))}
          </DataTable>
        </section>
      )}

      {/* Spending By Vendor */}
      {spending && spending.breakdown && spending.breakdown.length > 0 && (
        <section>
          <h2 className="mb-3 font-display text-base font-semibold">Spending by Vendor</h2>
          <DataTable columns={["Vendor", "PO Count", "Total Amount", "% of Total"]}>
            {spending.breakdown.map((v: any) => (
              <Tr key={v.vendorId}>
                <Td className="font-medium">{v.vendorName}</Td>
                <Td>{v.poCount}</Td>
                <Td className="font-mono">{formatAmount(v.totalAmount)}</Td>
                <Td>{v.percentage}%</Td>
              </Tr>
            ))}
          </DataTable>
        </section>
      )}
    </Layout>
  );
}
