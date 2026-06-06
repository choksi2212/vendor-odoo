import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { StatusBadge } from "@/components/Badge";
import { LinkButton } from "@/components/Button";
import { quotationAPI } from "@/lib/api/endpoints";
import { Loader2, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/quotations/")({ component: QuotationsPage });

interface Quotation {
  id: string;
  rfqId: string;
  rfqTitle: string;
  unitPrice: number;
  totalPrice: number;
  deliveryDays: number;
  status: string;
  submittedAt?: string;
}

function QuotationsPage() {
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadQuotations();
  }, []);

  const loadQuotations = async () => {
    try {
      setLoading(true);
      setError("");
      // Backend filters by current vendor automatically
      const data = await quotationAPI.list();
      setQuotations(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.message || "Failed to load quotations");
    } finally {
      setLoading(false);
    }
  };

  // Loading State
  if (loading) {
    return (
      <Layout>
        <PageHeader
          title="My Quotations"
          breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Quotations" }]}
        />
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading your quotations...
        </div>
      </Layout>
    );
  }

  // Error State
  if (error) {
    return (
      <Layout>
        <PageHeader
          title="My Quotations"
          breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Quotations" }]}
        />
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">{error}</span>
          </div>
          <button
            onClick={loadQuotations}
            className="mt-3 rounded-md bg-white px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100"
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
        title="My Quotations"
        breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Quotations" }]}
      />

      {/* Empty State */}
      {quotations.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border bg-muted/20 p-12 text-center">
          <p className="text-muted-foreground">
            No quotations yet. Wait for RFQs to be assigned to you.
          </p>
        </div>
      ) : (
        <DataTable columns={["RFQ Title", "Status", "My Quoted Price", "Delivery Days", "Actions"]}>
          {quotations.map((q) => (
            <Tr key={q.id}>
              <Td>
                <div className="font-medium">{q.rfqTitle}</div>
                <div className="text-xs text-muted-foreground">{q.rfqId}</div>
              </Td>
              <Td>
                <StatusBadge status={q.status} />
              </Td>
              <Td>
                {q.unitPrice ? (
                  `₹${q.unitPrice.toLocaleString("en-IN")}`
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </Td>
              <Td>
                {q.deliveryDays ? (
                  `${q.deliveryDays} days`
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </Td>
              <Td>
                {q.status === "draft" || q.status === "pending" ? (
                  <LinkButton to="/quotations/submit/$rfqId" params={{ rfqId: q.rfqId }}>
                    {q.status === "draft" ? "Continue" : "Submit Quote"}
                  </LinkButton>
                ) : (
                  <LinkButton to="/rfq/$id" params={{ id: q.rfqId }} variant="ghost">
                    View RFQ
                  </LinkButton>
                )}
              </Td>
            </Tr>
          ))}
        </DataTable>
      )}
    </Layout>
  );
}
