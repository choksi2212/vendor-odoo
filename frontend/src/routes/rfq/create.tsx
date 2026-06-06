import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { Button } from "@/components/Button";
import { Field, inputCls } from "@/components/AuthShell";
import { FormSection } from "../vendors/add";
import { rfqAPI, vendorAPI } from "@/lib/api/endpoints";
import { useAuth } from "@/context/AuthContext";
import { Loader2, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/rfq/create")({ component: CreateRFQ });

interface Vendor {
  id: string;
  name: string;
  category: string;
  rating: number;
  status: string;
}

function CreateRFQ() {
  const nav = useNavigate();
  const { role } = useAuth();
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loadingVendors, setLoadingVendors] = useState(true);
  const [selectedVendors, setSelectedVendors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Redirect vendors away from this page
  useEffect(() => {
    if (role === "Vendor") {
      nav({ to: "/rfq" });
    }
  }, [role, nav]);

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [deadline, setDeadline] = useState("");
  const [productName, setProductName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState("units");

  useEffect(() => {
    if (role !== "Vendor") {
      loadVendors();
    }
  }, [role]);

  const loadVendors = async () => {
    try {
      setLoadingVendors(true);
      const data = await vendorAPI.list({ status: "active" });
      setVendors(Array.isArray(data) ? data : (data?.items || []));
    } catch (err: any) {
      console.error("Failed to load vendors:", err);
    } finally {
      setLoadingVendors(false);
    }
  };

  const toggleVendor = (vendorId: string) => {
    setSelectedVendors((prev) =>
      prev.includes(vendorId) ? prev.filter((id) => id !== vendorId) : [...prev, vendorId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    if (!productName.trim()) {
      setError("Product name is required");
      return;
    }
    if (!quantity || Number(quantity) <= 0) {
      setError("Quantity must be greater than 0");
      return;
    }
    if (!deadline) {
      setError("Deadline is required");
      return;
    }
    if (selectedVendors.length === 0) {
      setError("Please select at least one vendor");
      return;
    }

    try {
      setSubmitting(true);

      // Create RFQ
      const rfqData = {
        title: title.trim(),
        description: description.trim(),
        productName: productName.trim(),
        quantity: Number(quantity),
        unit,
        deadline,
      };

      const createdRFQ = await rfqAPI.create(rfqData);

      // Assign vendors to RFQ
      await rfqAPI.assignVendors(createdRFQ.id, selectedVendors);

      // Navigate to RFQ list
      nav({ to: "/rfq" });
    } catch (err: any) {
      setError(err.message || "Failed to create RFQ");
      setSubmitting(false);
    }
  };

  return (
    <Layout>
      <PageHeader
        title="Create RFQ"
        breadcrumb={[{ label: "RFQs", to: "/rfq" }, { label: "New" }]}
        actions={
          <>
            <Button variant="secondary" onClick={() => nav({ to: "/rfq" })} disabled={submitting}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Submit RFQ"
              )}
            </Button>
          </>
        }
      />

      {/* Error Message */}
      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      <form className="space-y-8 rounded-lg border border-border bg-card p-6" onSubmit={handleSubmit}>
        <FormSection title="RFQ Details" desc="Title, summary and submission deadline.">
          <div className="space-y-4">
            <Field label="Title">
              <input
                className={inputCls}
                required
                placeholder="e.g. Annual Office Stationery Procurement"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </Field>
            <Field label="Description">
              <textarea
                rows={4}
                className={inputCls}
                placeholder="Scope, technical specs, terms…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </Field>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="Deadline">
                <input
                  type="date"
                  className={inputCls}
                  required
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                  min={new Date().toISOString().split("T")[0]}
                />
              </Field>
              <Field label="Attachment">
                <input type="file" className="text-xs text-muted-foreground" />
                <p className="mt-1 text-xs text-muted-foreground">Optional: Upload specs or requirements</p>
              </Field>
            </div>
          </div>
        </FormSection>

        <FormSection title="Product / Service" desc="What you're sourcing and how much.">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="md:col-span-2">
              <Field label="Product Name">
                <input
                  className={inputCls}
                  required
                  placeholder="e.g. A4 Copy Paper"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                />
              </Field>
            </div>
            <Field label="Quantity">
              <input
                type="number"
                className={inputCls}
                required
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </Field>
            <Field label="Unit">
              <select className={inputCls} value={unit} onChange={(e) => setUnit(e.target.value)}>
                <option value="units">units</option>
                <option value="kits">kits</option>
                <option value="litres">litres</option>
                <option value="kg">kg</option>
                <option value="contract">contract</option>
              </select>
            </Field>
          </div>
        </FormSection>

        <FormSection title="Vendor Assignment" desc="Invite vendors to submit their quotations.">
          {loadingVendors ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Loading vendors...
            </div>
          ) : vendors.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border bg-muted/20 p-8 text-center text-muted-foreground">
              No active vendors available. Please add vendors first.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                {vendors.map((v) => (
                  <label
                    key={v.id}
                    className={`flex cursor-pointer items-center gap-3 rounded-md border p-3 text-sm transition-colors ${
                      selectedVendors.includes(v.id)
                        ? "border-[color:var(--action)] bg-[color:var(--action)]/5"
                        : "border-border hover:bg-muted/40"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedVendors.includes(v.id)}
                      onChange={() => toggleVendor(v.id)}
                    />
                    <div className="flex-1">
                      <p className="font-medium">{v.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(v.category as any)?.name || (typeof v.category === 'string' ? v.category : '-')} · ★ {v.rating ? v.rating.toFixed(1) : "N/A"}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
              {selectedVendors.length > 0 && (
                <p className="mt-3 text-xs text-muted-foreground">
                  {selectedVendors.length} vendor(s) will be invited to submit quotations.
                </p>
              )}
            </>
          )}
        </FormSection>
      </form>
    </Layout>
  );
}
