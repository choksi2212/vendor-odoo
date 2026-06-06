import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { StatusBadge } from "@/components/Badge";
import { Button, LinkButton } from "@/components/Button";
import { rfqAPI } from "@/lib/api/endpoints";
import { inputCls } from "@/components/AuthShell";
import { Loader2, Search, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/rfq/")({ component: RFQList });

interface RFQ {
  id: string;
  title: string;
  description: string;
  productName: string;
  quantity: number;
  unit: string;
  deadline: string;
  status: string;
  assignedVendors: Array<{ id: string; name: string }>;
  createdAt: string;
}

function RFQList() {
  const nav = useNavigate();
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    loadRFQs();
  }, []);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!loading) loadRFQs();
    }, 300);
    return () => clearTimeout(timer);
  }, [search, statusFilter]);

  const loadRFQs = async () => {
    try {
      setLoading(true);
      setError("");
      const params: any = {};
      if (search) params.search = search;
      if (statusFilter !== "all") params.status = statusFilter;
      const data = await rfqAPI.list(params);
      setRfqs(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.message || "Failed to load RFQs");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <Layout>
      <PageHeader
        title="Request for Quotations"
        breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "RFQs" }]}
        actions={<Button onClick={() => nav({ to: "/rfq/create" })}>+ Create RFQ</Button>}
      />

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search RFQs by title or product..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`${inputCls} pl-10`}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={`${inputCls} w-auto min-w-[150px]`}
        >
          <option value="all">All Status</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {/* Loading State */}
      {loading && rfqs.length === 0 && (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading RFQs...
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">Error loading RFQs</span>
          </div>
          <p className="mt-1 text-sm">{error}</p>
          <Button onClick={loadRFQs} variant="secondary" className="mt-3">
            Retry
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && rfqs.length === 0 && (
        <div className="rounded-lg border border-dashed border-border bg-muted/20 p-12 text-center">
          <p className="text-muted-foreground">
            {search || statusFilter !== "all"
              ? "No RFQs match your filters"
              : "No RFQs yet. Create one to get started!"}
          </p>
          {!search && statusFilter === "all" && (
            <Button onClick={() => nav({ to: "/rfq/create" })} className="mt-4">
              + Create First RFQ
            </Button>
          )}
        </div>
      )}

      {/* Data Table */}
      {!loading && !error && rfqs.length > 0 && (
        <DataTable columns={["RFQ Title", "Product", "Quantity", "Deadline", "Vendors", "Status", "Actions"]}>
          {rfqs.map((r) => (
            <Tr key={r.id}>
              <Td>
                <div className="font-medium">{r.title}</div>
                <div className="text-xs text-muted-foreground">{r.id}</div>
              </Td>
              <Td>{r.productName}</Td>
              <Td>
                {r.quantity} {r.unit}
              </Td>
              <Td className="text-muted-foreground">{formatDate(r.deadline)}</Td>
              <Td>
                <div className="flex flex-wrap gap-1">
                  {r.assignedVendors && r.assignedVendors.length > 0 ? (
                    <>
                      {r.assignedVendors.slice(0, 2).map((v) => (
                        <span key={v.id} className="rounded bg-muted px-1.5 py-0.5 text-xs">
                          {v.name.split(" ")[0]}
                        </span>
                      ))}
                      {r.assignedVendors.length > 2 && (
                        <span className="text-xs text-muted-foreground">
                          +{r.assignedVendors.length - 2}
                        </span>
                      )}
                    </>
                  ) : (
                    <span className="text-xs text-muted-foreground">No vendors</span>
                  )}
                </div>
              </Td>
              <Td>
                <StatusBadge status={r.status} />
              </Td>
              <Td>
                <div className="flex gap-2">
                  <LinkButton to="/rfq/$id" params={{ id: r.id }} variant="ghost">
                    View
                  </LinkButton>
                  {r.assignedVendors && r.assignedVendors.length > 0 && (
                    <LinkButton to="/rfq/$id/compare" params={{ id: r.id }} variant="ghost">
                      Compare
                    </LinkButton>
                  )}
                </div>
              </Td>
            </Tr>
          ))}
        </DataTable>
      )}

      {/* Inline Loading during Filter */}
      {loading && rfqs.length > 0 && (
        <div className="mt-4 flex items-center justify-center text-sm text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Updating...
        </div>
      )}
    </Layout>
  );
}
