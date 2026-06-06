import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { Button } from "@/components/Button";
import { rfqAPI, quotationAPI } from "@/lib/api/endpoints";
import { Loader2, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/rfq/$id/compare")({
  component: CompareQuotations,
});

type SortBy = "price" | "delivery" | "rating" | "vendor";
type SortOrder = "asc" | "desc";

interface RFQ {
  id: string;
  title: string;
  quantity: number;
  unit: string;
}

interface Quotation {
  id: string;
  rfqId: string;
  vendorName: string;
  vendorRating: number;
  unitPrice: number;
  totalPrice: number;
  deliveryDays: number;
  warranty: string;
  certifications: string;
  notes: string;
  status: string;
}

function CompareQuotations() {
  const { id } = Route.useParams();
  const nav = useNavigate();
  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [sortBy, setSortBy] = useState<SortBy>("price");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [filterRating, setFilterRating] = useState<number>(0);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      const [rfqData, comparisonData] = await Promise.all([
        rfqAPI.getById(id),
        quotationAPI.compareForRFQ(id),
      ]);
      setRfq(rfqData);
      setQuotations(Array.isArray(comparisonData) ? comparisonData : (comparisonData?.items || []));
    } catch (err: any) {
      setError(err.message || "Failed to load comparison data");
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (newSortBy: SortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(newSortBy);
      setSortOrder("asc");
    }
  };

  // Loading State
  if (loading) {
    return (
      <Layout>
        <PageHeader
          title="Compare Quotations"
          breadcrumb={[{ label: "RFQs", to: "/rfq" }, { label: id }, { label: "Compare" }]}
        />
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading comparison data...
        </div>
      </Layout>
    );
  }

  // Error State
  if (error) {
    return (
      <Layout>
        <PageHeader
          title="Compare Quotations"
          breadcrumb={[{ label: "RFQs", to: "/rfq" }, { label: id }, { label: "Compare" }]}
        />
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">{error}</span>
          </div>
          <Button onClick={loadData} variant="secondary" className="mt-3">
            Retry
          </Button>
          <Button onClick={() => nav({ to: `/rfq/${id}` })} variant="secondary" className="ml-2 mt-3">
            Back to RFQ
          </Button>
        </div>
      </Layout>
    );
  }

  // Empty State
  if (!rfq || quotations.length === 0) {
    return (
      <Layout>
        <PageHeader
          title="Compare Quotations"
          breadcrumb={[{ label: "RFQs", to: "/rfq" }, { label: id }, { label: "Compare" }]}
        />
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <p className="text-muted-foreground">No quotations available to compare.</p>
          <Button className="mt-4" onClick={() => nav({ to: `/rfq/${id}` })}>
            Back to RFQ
          </Button>
        </div>
      </Layout>
    );
  }

  // Filter by rating
  const filteredQuotations = filterRating > 0
    ? quotations.filter((q) => (q.vendorRating || 0) >= filterRating)
    : quotations;

  // Sort quotations
  const sortedQuotations = [...filteredQuotations].sort((a, b) => {
    let comparison = 0;
    switch (sortBy) {
      case "price":
        comparison = a.unitPrice - b.unitPrice;
        break;
      case "delivery":
        comparison = a.deliveryDays - b.deliveryDays;
        break;
      case "rating":
        comparison = (b.vendorRating || 0) - (a.vendorRating || 0); // Higher rating first
        break;
      case "vendor":
        comparison = a.vendorName.localeCompare(b.vendorName);
        break;
    }
    return sortOrder === "asc" ? comparison : -comparison;
  });

  // Calculate best values
  const lowestPrice = Math.min(...filteredQuotations.map((q) => q.unitPrice));
  const fastestDelivery = Math.min(...filteredQuotations.map((q) => q.deliveryDays));
  const highestRating = Math.max(...filteredQuotations.map((q) => q.vendorRating || 0));

  return (
    <Layout>
      <PageHeader
        title={`Compare Quotations — ${rfq.title}`}
        breadcrumb={[
          { label: "RFQs", to: "/rfq" },
          { label: id, to: `/rfq/${id}` },
          { label: "Compare" },
        ]}
        actions={
          <>
            <Button variant="secondary" onClick={() => nav({ to: `/rfq/${id}` })}>
              Back to RFQ
            </Button>
            <Button onClick={() => alert("Select a quotation to proceed to approval")}>
              Proceed to Approval
            </Button>
          </>
        }
      />

      {/* Summary Cards */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Total Quotations</p>
          <p className="mt-1 font-display text-2xl font-bold text-foreground">
            {filteredQuotations.length}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">vendors responded</p>
        </div>
        <div className="rounded-lg border border-green-600/20 bg-green-50 p-4 dark:bg-green-950/20">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Best Price</p>
          <p className="mt-1 font-display text-2xl font-bold text-green-600">
            ₹{lowestPrice.toLocaleString("en-IN")}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">per unit</p>
        </div>
        <div className="rounded-lg border border-blue-600/20 bg-blue-50 p-4 dark:bg-blue-950/20">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Fastest Delivery</p>
          <p className="mt-1 font-display text-2xl font-bold text-blue-600">
            {fastestDelivery} days
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">delivery time</p>
        </div>
      </div>

      {/* Filters & Sorting */}
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card p-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">Sort by:</span>
          <button
            onClick={() => handleSort("price")}
            className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
              sortBy === "price"
                ? "bg-[color:var(--action)] text-[color:var(--action-foreground)]"
                : "bg-muted text-muted-foreground hover:bg-muted/70"
            }`}
          >
            Price {sortBy === "price" && (sortOrder === "asc" ? "↑" : "↓")}
          </button>
          <button
            onClick={() => handleSort("delivery")}
            className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
              sortBy === "delivery"
                ? "bg-[color:var(--action)] text-[color:var(--action-foreground)]"
                : "bg-muted text-muted-foreground hover:bg-muted/70"
            }`}
          >
            Delivery {sortBy === "delivery" && (sortOrder === "asc" ? "↑" : "↓")}
          </button>
          <button
            onClick={() => handleSort("rating")}
            className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
              sortBy === "rating"
                ? "bg-[color:var(--action)] text-[color:var(--action-foreground)]"
                : "bg-muted text-muted-foreground hover:bg-muted/70"
            }`}
          >
            Rating {sortBy === "rating" && (sortOrder === "asc" ? "↑" : "↓")}
          </button>
          <button
            onClick={() => handleSort("vendor")}
            className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
              sortBy === "vendor"
                ? "bg-[color:var(--action)] text-[color:var(--action-foreground)]"
                : "bg-muted text-muted-foreground hover:bg-muted/70"
            }`}
          >
            Vendor {sortBy === "vendor" && (sortOrder === "asc" ? "↑" : "↓")}
          </button>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">Min Rating:</span>
          <select
            value={filterRating}
            onChange={(e) => setFilterRating(Number(e.target.value))}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
          >
            <option value="0">All</option>
            <option value="4.0">4.0+</option>
            <option value="4.5">4.5+</option>
          </select>
        </div>
      </div>

      {/* Comparison Table - Side by Side */}
      <div className="overflow-x-auto rounded-lg border border-border bg-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="sticky left-0 z-10 bg-muted/40 px-4 py-3 text-left font-semibold">
                Criteria
              </th>
              {sortedQuotations.map((q) => (
                <th
                  key={q.id}
                  className="min-w-[200px] border-l border-border px-4 py-3 text-center font-semibold"
                >
                  <div className="font-display text-base">{q.vendorName}</div>
                  <div className="mt-1 text-xs font-normal text-muted-foreground">{q.id}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Unit Price Row */}
            <tr className="border-b border-border hover:bg-muted/20">
              <td className="sticky left-0 z-10 bg-card px-4 py-3 font-medium">
                Unit Price
                <div className="text-xs font-normal text-muted-foreground">per unit</div>
              </td>
              {sortedQuotations.map((q) => (
                <td
                  key={q.id}
                  className={`border-l border-border px-4 py-3 text-center font-display text-lg font-bold ${
                    q.unitPrice === lowestPrice
                      ? "bg-green-50 text-green-600 dark:bg-green-950/30"
                      : ""
                  }`}
                >
                  ₹{q.unitPrice.toLocaleString("en-IN")}
                  {q.unitPrice === lowestPrice && (
                    <div className="mt-1 text-xs font-semibold uppercase tracking-wide text-green-600">
                      ✓ Lowest Price
                    </div>
                  )}
                </td>
              ))}
            </tr>

            {/* Total Price Row */}
            <tr className="border-b border-border hover:bg-muted/20">
              <td className="sticky left-0 z-10 bg-card px-4 py-3 font-medium">
                Total Amount
                <div className="text-xs font-normal text-muted-foreground">
                  for {rfq.quantity} {rfq.unit}
                </div>
              </td>
              {sortedQuotations.map((q) => (
                <td
                  key={q.id}
                  className="border-l border-border px-4 py-3 text-center font-display text-base font-semibold"
                >
                  ₹{q.totalPrice.toLocaleString("en-IN")}
                </td>
              ))}
            </tr>

            {/* Delivery Timeline Row */}
            <tr className="border-b border-border hover:bg-muted/20">
              <td className="sticky left-0 z-10 bg-card px-4 py-3 font-medium">
                Delivery Time
                <div className="text-xs font-normal text-muted-foreground">working days</div>
              </td>
              {sortedQuotations.map((q) => (
                <td
                  key={q.id}
                  className={`border-l border-border px-4 py-3 text-center font-display text-lg font-bold ${
                    q.deliveryDays === fastestDelivery
                      ? "bg-blue-50 text-blue-600 dark:bg-blue-950/30"
                      : ""
                  }`}
                >
                  {q.deliveryDays} days
                  {q.deliveryDays === fastestDelivery && (
                    <div className="mt-1 text-xs font-semibold uppercase tracking-wide text-blue-600">
                      ⚡ Fastest
                    </div>
                  )}
                </td>
              ))}
            </tr>

            {/* Vendor Rating Row */}
            <tr className="border-b border-border hover:bg-muted/20">
              <td className="sticky left-0 z-10 bg-card px-4 py-3 font-medium">
                Vendor Rating
                <div className="text-xs font-normal text-muted-foreground">out of 5.0</div>
              </td>
              {sortedQuotations.map((q) => {
                const rating = q.vendorRating || 0;
                return (
                  <td
                    key={q.id}
                    className={`border-l border-border px-4 py-3 text-center ${
                      rating === highestRating && rating > 0
                        ? "bg-amber-50 dark:bg-amber-950/30"
                        : ""
                    }`}
                  >
                    {rating > 0 ? (
                      <>
                        <div className="flex items-center justify-center gap-1">
                          <span className="text-xl text-amber-500">
                            {"★".repeat(Math.floor(rating))}
                          </span>
                          <span className="text-xl text-muted-foreground">
                            {"★".repeat(5 - Math.floor(rating))}
                          </span>
                        </div>
                        <div className="mt-1 font-display text-base font-semibold">
                          {rating.toFixed(1)}
                        </div>
                        {rating === highestRating && rating > 0 && (
                          <div className="mt-1 text-xs font-semibold uppercase tracking-wide text-amber-600">
                            ⭐ Top Rated
                          </div>
                        )}
                      </>
                    ) : (
                      <span className="text-muted-foreground">N/A</span>
                    )}
                  </td>
                );
              })}
            </tr>

            {/* Warranty Row */}
            <tr className="border-b border-border hover:bg-muted/20">
              <td className="sticky left-0 z-10 bg-card px-4 py-3 font-medium">
                Warranty Period
              </td>
              {sortedQuotations.map((q) => (
                <td key={q.id} className="border-l border-border px-4 py-3 text-center">
                  {q.warranty || "N/A"}
                </td>
              ))}
            </tr>

            {/* Certifications Row */}
            <tr className="border-b border-border hover:bg-muted/20">
              <td className="sticky left-0 z-10 bg-card px-4 py-3 font-medium">
                Certifications
              </td>
              {sortedQuotations.map((q) => (
                <td key={q.id} className="border-l border-border px-4 py-3 text-center text-xs">
                  {q.certifications || "None"}
                </td>
              ))}
            </tr>

            {/* Notes Row */}
            <tr className="hover:bg-muted/20">
              <td className="sticky left-0 z-10 bg-card px-4 py-3 font-medium">Notes</td>
              {sortedQuotations.map((q) => (
                <td
                  key={q.id}
                  className="border-l border-border px-4 py-3 text-center text-xs text-muted-foreground"
                >
                  {q.notes || "—"}
                </td>
              ))}
            </tr>

            {/* Action Row */}
            <tr className="bg-muted/20">
              <td className="sticky left-0 z-10 bg-muted/40 px-4 py-4 font-medium">Action</td>
              {sortedQuotations.map((q) => (
                <td key={q.id} className="border-l border-border px-4 py-4 text-center">
                  <Button
                    onClick={() => {
                      alert(`Selecting quotation ${q.id} from ${q.vendorName}`);
                      nav({ to: "/approvals" });
                    }}
                  >
                    Select This
                  </Button>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-green-600"></div>
          <span>Lowest Price</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-blue-600"></div>
          <span>Fastest Delivery</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-amber-500"></div>
          <span>Highest Rating</span>
        </div>
      </div>
    </Layout>
  );
}

