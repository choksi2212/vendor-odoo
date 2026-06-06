import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { Button } from "@/components/Button";
import { Field, inputCls } from "@/components/AuthShell";
import { FormSection } from "../../vendors/add";
import { rfqAPI, quotationAPI } from "@/lib/api/endpoints";
import { Loader2, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/quotations/submit/$rfqId")({ component: SubmitQuote });

interface RFQ {
  id: string;
  title: string;
  description: string;
  productName: string;
  quantity: number;
  unit: string;
  deadline: string;
  status: string;
}

function SubmitQuote() {
  const { rfqId } = Route.useParams();
  const nav = useNavigate();
  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [vendorProfile, setVendorProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Form state
  const [unitPrice, setUnitPrice] = useState<number>(0);
  const [deliveryDays, setDeliveryDays] = useState<number>(0);
  const [validityDays, setValidityDays] = useState<number>(30);
  const [warranty, setWarranty] = useState("");
  const [certifications, setCertifications] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    loadData();
  }, [rfqId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      
      // Load RFQ and vendor profile
      const [rfqData, profileResponse] = await Promise.all([
        rfqAPI.getById(rfqId),
        fetch("/api/users/me/vendor-profile", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        }),
      ]);
      
      setRfq(rfqData);
      const profileData = await profileResponse.json();
      setVendorProfile(profileData);
      
      if (!profileData.has_vendor_entity) {
        setError("Your user account is not linked to a vendor entity. Please contact the administrator.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!vendorProfile?.has_vendor_entity) {
      setError("Vendor profile not found. Please contact administrator.");
      return;
    }
    if (!unitPrice || unitPrice <= 0) {
      setError("Unit price must be greater than 0");
      return;
    }
    if (!deliveryDays || deliveryDays <= 0) {
      setError("Delivery days must be greater than 0");
      return;
    }

    try {
      setSubmitting(true);

      const quotationData = {
        rfqId,
        vendorId: vendorProfile.vendor_id,
        unitPrice: unitPrice.toString(),
        deliveryDays,
        notes: notes.trim() || null,
      };

      // Create quotation (creates as draft)
      const created = await quotationAPI.create(quotationData);

      // Submit the quotation
      await quotationAPI.submit(created.id);

      // Navigate back to quotations list
      nav({ to: "/quotations" });
    } catch (err: any) {
      setError(err.message || "Failed to submit quotation");
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  // Loading State
  if (loading) {
    return (
      <Layout>
        <PageHeader
          title="Submit Quotation"
          breadcrumb={[{ label: "My Quotations", to: "/quotations" }, { label: rfqId }]}
        />
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading RFQ details...
        </div>
      </Layout>
    );
  }

  // Error State
  if (error && !rfq) {
    return (
      <Layout>
        <PageHeader
          title="Submit Quotation"
          breadcrumb={[{ label: "My Quotations", to: "/quotations" }, { label: rfqId }]}
        />
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">{error}</span>
          </div>
          <Button onClick={loadData} variant="secondary" className="mt-3">
            Retry
          </Button>
          <Button onClick={() => nav({ to: "/quotations" })} variant="secondary" className="ml-2 mt-3">
            Back to Quotations
          </Button>
        </div>
      </Layout>
    );
  }

  if (!rfq) return null;

  const totalPrice = unitPrice * rfq.quantity;

  return (
    <Layout>
      <PageHeader
        title={`Submit Quotation — ${rfq.id}`}
        breadcrumb={[{ label: "My Quotations", to: "/quotations" }, { label: rfq.id }]}
        actions={
          <>
            <Button variant="secondary" onClick={() => nav({ to: "/quotations" })} disabled={submitting}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                "Submit Quotation"
              )}
            </Button>
          </>
        }
      />

      {/* Error Message */}
      {error && rfq && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      <form className="space-y-8 rounded-lg border border-border bg-card p-6" onSubmit={handleSubmit}>
        <FormSection title="RFQ Summary">
          <div className="rounded-md bg-muted/40 p-4 text-sm">
            <p className="font-semibold">{rfq.title}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {rfq.productName} · {rfq.quantity} {rfq.unit} · Deadline: {formatDate(rfq.deadline)}
            </p>
            {rfq.description && (
              <p className="mt-2 text-xs text-muted-foreground">{rfq.description}</p>
            )}
          </div>
        </FormSection>

        <FormSection title="Your Pricing">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label={`Unit Price (₹ per ${rfq.unit.replace(/s$/, "")})`}>
              <input
                type="number"
                className={inputCls}
                value={unitPrice || ""}
                onChange={(e) => setUnitPrice(Number(e.target.value))}
                required
                min="0.01"
                step="0.01"
                placeholder="0.00"
              />
            </Field>
            <Field label="Total Price (auto-calculated)">
              <input
                className={`${inputCls} bg-muted/40`}
                readOnly
                value={`₹${totalPrice.toLocaleString("en-IN", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`}
              />
            </Field>
            <Field label="Delivery Timeline (days)">
              <input
                type="number"
                className={inputCls}
                value={deliveryDays || ""}
                onChange={(e) => setDeliveryDays(Number(e.target.value))}
                required
                min="1"
                placeholder="e.g., 15"
              />
            </Field>
            <Field label="Quotation Validity (days)">
              <input
                type="number"
                className={inputCls}
                value={validityDays}
                onChange={(e) => setValidityDays(Number(e.target.value))}
                min="1"
                placeholder="e.g., 30"
              />
            </Field>
          </div>
        </FormSection>

        <FormSection title="Additional Information" desc="Optional details to strengthen your quotation">
          <div className="space-y-4">
            <Field label="Warranty Period">
              <input
                type="text"
                className={inputCls}
                value={warranty}
                onChange={(e) => setWarranty(e.target.value)}
                placeholder="e.g., 12 months manufacturer warranty"
              />
            </Field>
            <Field label="Certifications">
              <input
                type="text"
                className={inputCls}
                value={certifications}
                onChange={(e) => setCertifications(e.target.value)}
                placeholder="e.g., ISO 9001, BIS certified"
              />
            </Field>
            <Field label="Notes / Comments">
              <textarea
                rows={3}
                className={inputCls}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Payment terms, special conditions, bulk discounts, etc."
              />
            </Field>
          </div>
        </FormSection>

        {/* Info Box */}
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
          <p className="font-medium">Before you submit:</p>
          <ul className="mt-2 list-inside list-disc space-y-1 text-xs">
            <li>Double-check your pricing and delivery timeline</li>
            <li>Ensure all required fields are filled accurately</li>
            <li>Once submitted, you may not be able to edit your quotation</li>
            <li>The procurement officer will review and compare all quotations</li>
          </ul>
        </div>
      </form>
    </Layout>
  );
}
