import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { Button, LinkButton } from "@/components/Button";
import { StatusBadge } from "@/components/Badge";
import { DataTable, Td, Tr } from "@/components/Table";
import { rfqAPI, quotationAPI } from "@/lib/api/endpoints";
import { useAuth } from "@/context/AuthContext";
import { Loader2, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/rfq/$id/")({ component: RFQDetail });

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

interface Quotation {
  id: string;
  rfqId: string;
  vendorName: string;
  unitPrice: number;
  totalPrice: number;
  deliveryDays: number;
  status: string;
  submittedAt: string;
}

function RFQDetail() {
  const { id } = Route.useParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      const [rfqData, quotationsData] = await Promise.all([
        rfqAPI.getById(id),
        quotationAPI.listForRFQ(id),
      ]);
      setRfq(rfqData);
      setQuotations(Array.isArray(quotationsData) ? quotationsData : []);
    } catch (err: any) {
      setError(err.message || "Failed to load RFQ details");
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

  const getCurrentWorkflowStep = (status: string) => {
    const steps = ["draft", "published", "quotations_received", "comparison", "approved", "po_generated"];
    return steps.indexOf(status.toLowerCase());
  };

  // Loading State
  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading RFQ details...
        </div>
      </Layout>
    );
  }

  // Error State
  if (error || !rfq) {
    return (
      <Layout>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">{error || "RFQ not found"}</span>
          </div>
          <Button onClick={loadData} variant="secondary" className="mt-3">
            Retry
          </Button>
          <Button onClick={() => nav({ to: "/rfq" })} variant="secondary" className="ml-2 mt-3">
            Back to List
          </Button>
        </div>
      </Layout>
    );
  }

  const currentStep = getCurrentWorkflowStep(rfq.status);

  return (
    <Layout>
      <PageHeader
        title={rfq.title}
        breadcrumb={[{ label: "RFQs", to: "/rfq" }, { label: rfq.id }]}
        actions={
          <>
            <Button variant="secondary" onClick={() => nav({ to: "/rfq" })}>
              Back
            </Button>
            {quotations.length > 0 && (
              <LinkButton to="/rfq/$id/compare" params={{ id: rfq.id }}>
                Compare {quotations.length} Quotation{quotations.length !== 1 ? "s" : ""}
              </LinkButton>
            )}
            {user?.role === "procurement_officer" && quotations.length > 0 && (
              <Button onClick={() => nav({ to: "/approvals" })}>Initiate Approval</Button>
            )}
          </>
        }
      />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 lg:col-span-2">
          <div className="flex items-start justify-between border-b border-border pb-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">RFQ Reference</p>
              <p className="font-display text-lg font-semibold">{rfq.id}</p>
            </div>
            <StatusBadge status={rfq.status} />
          </div>
          <dl className="mt-5 grid grid-cols-1 gap-x-8 gap-y-4 md:grid-cols-2">
            <Item k="Product" v={rfq.productName} />
            <Item k="Quantity" v={`${rfq.quantity} ${rfq.unit}`} />
            <Item k="Deadline" v={formatDate(rfq.deadline)} />
            <Item
              k="Invited Vendors"
              v={
                rfq.assignedVendors && rfq.assignedVendors.length > 0
                  ? rfq.assignedVendors.map((v) => v.name).join(", ")
                  : "No vendors assigned"
              }
            />
            <div className="md:col-span-2">
              <Item k="Description" v={rfq.description || "No description provided"} />
            </div>
            <Item k="Created" v={formatDate(rfq.createdAt)} />
          </dl>
        </div>
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="font-display text-sm font-semibold">Workflow</h3>
          <ol className="mt-4 space-y-3 text-sm">
            {[
              "Created",
              "Quotations Received",
              "Comparison",
              "Approval",
              "PO Generated",
              "Invoice Issued",
            ].map((s, i) => (
              <li key={s} className="flex items-center gap-3">
                <span
                  className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
                    i <= currentStep
                      ? "bg-[color:var(--action)] text-white"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {i + 1}
                </span>
                <span className={i <= currentStep ? "text-foreground" : "text-muted-foreground"}>{s}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>

      <div className="mb-3 mt-8 flex items-center justify-between">
        <h2 className="font-display text-base font-semibold">
          Quotations Received ({quotations.length})
        </h2>
        {quotations.length > 1 && (
          <LinkButton to="/rfq/$id/compare" params={{ id: rfq.id }} variant="ghost">
            View Side-by-Side Comparison →
          </LinkButton>
        )}
      </div>
      <DataTable
        columns={["Vendor", "Unit Price", "Total", "Delivery Days", "Status"]}
        empty={quotations.length === 0}
      >
        {quotations.map((q) => (
          <Tr key={q.id}>
            <Td className="font-medium">{q.vendorName}</Td>
            <Td>₹{q.unitPrice.toLocaleString("en-IN")}</Td>
            <Td className="font-semibold">₹{q.totalPrice.toLocaleString("en-IN")}</Td>
            <Td>{q.deliveryDays} days</Td>
            <Td>
              <StatusBadge status={q.status} />
            </Td>
          </Tr>
        ))}
      </DataTable>
    </Layout>
  );
}

function Item({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{k}</dt>
      <dd className="mt-1 text-sm text-foreground">{v}</dd>
    </div>
  );
}
