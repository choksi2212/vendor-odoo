import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { Button } from "@/components/Button";
import { Field, inputCls } from "@/components/AuthShell";
import { vendorAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/vendors/add")({ component: AddVendor });

function AddVendor() {
  const nav = useNavigate();
  const [categories, setCategories] = useState<any[]>([]);
  const [f, setF] = useState({
    name: "",
    categoryId: "",
    gstNumber: "",
    email: "",
    phone: "",
    address: "",
    status: "active"
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await vendorAPI.getCategories();
      setCategories(data || []);
      if (data && data.length > 0) {
        setF(prev => ({ ...prev, categoryId: data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const u = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setF({ ...f, [k]: e.target.value });
    // Clear validation error for this field
    if (validationErrors[k]) {
      setValidationErrors(prev => ({ ...prev, [k]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!f.name.trim()) errors.name = 'Vendor name is required';
    if (!f.email.trim()) errors.email = 'Email is required';
    if (f.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) {
      errors.email = 'Invalid email format';
    }
    if (f.gstNumber && !/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(f.gstNumber)) {
      errors.gstNumber = 'Invalid GST format (e.g., 27AABCU9603R1ZX)';
    }
    if (f.phone && !/^[0-9]{10}$/.test(f.phone.replace(/\D/g, ''))) {
      errors.phone = 'Phone must be 10 digits';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await vendorAPI.create({
        name: f.name,
        categoryId: f.categoryId,
        gstNumber: f.gstNumber,
        email: f.email,
        phone: f.phone || null,
        address: f.address || null,
        status: f.status,
      });

      // Success - navigate back to list
      nav({ to: "/vendors" });
    } catch (err: any) {
      console.error('Failed to create vendor:', err);
      setError(err.message || 'Failed to create vendor');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout>
      <PageHeader
        title="Add Vendor"
        breadcrumb={[{ label: "Vendors", to: "/vendors" }, { label: "New" }]}
        actions={
          <>
            <Button
              variant="secondary"
              onClick={() => nav({ to: "/vendors" })}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isSubmitting ? 'Saving...' : 'Save Vendor'}
            </Button>
          </>
        }
      />
      
      {error && (
        <div className="mb-4 rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <form className="space-y-8 rounded-lg border border-border bg-card p-6" onSubmit={handleSubmit}>
        <FormSection title="Company Information" desc="Legal entity details for vendor onboarding.">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="Vendor Name *">
              <input
                className={inputCls}
                required
                value={f.name}
                onChange={u("name")}
                placeholder="Acme Pvt Ltd"
                disabled={isSubmitting}
              />
              {validationErrors.name && (
                <p className="mt-1 text-xs text-red-600">{validationErrors.name}</p>
              )}
            </Field>
            
            <Field label="Category *">
              <select
                className={inputCls}
                value={f.categoryId}
                onChange={u("categoryId")}
                required
                disabled={isSubmitting}
              >
                {categories.length === 0 && <option>Loading...</option>}
                {categories.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </Field>
            
            <Field label="GST Number">
              <input
                className={inputCls}
                value={f.gstNumber}
                onChange={u("gstNumber")}
                placeholder="27AABCU9603R1ZX"
                disabled={isSubmitting}
              />
              {validationErrors.gstNumber && (
                <p className="mt-1 text-xs text-red-600">{validationErrors.gstNumber}</p>
              )}
            </Field>
            
            <Field label="Status">
              <select
                className={inputCls}
                value={f.status}
                onChange={u("status")}
                disabled={isSubmitting}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </Field>
          </div>
        </FormSection>
        
        <FormSection title="Contact Details" desc="Primary point of contact and location.">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="Email *">
              <input
                type="email"
                className={inputCls}
                required
                value={f.email}
                onChange={u("email")}
                placeholder="contact@acme.com"
                disabled={isSubmitting}
              />
              {validationErrors.email && (
                <p className="mt-1 text-xs text-red-600">{validationErrors.email}</p>
              )}
            </Field>
            
            <Field label="Phone">
              <input
                className={inputCls}
                value={f.phone}
                onChange={u("phone")}
                placeholder="9876543210"
                disabled={isSubmitting}
              />
              {validationErrors.phone && (
                <p className="mt-1 text-xs text-red-600">{validationErrors.phone}</p>
              )}
            </Field>
            
            <div className="md:col-span-2">
              <Field label="Address">
                <textarea
                  rows={3}
                  className={inputCls}
                  value={f.address}
                  onChange={u("address")}
                  placeholder="Office address"
                  disabled={isSubmitting}
                />
              </Field>
            </div>
          </div>
        </FormSection>
      </form>
    </Layout>
  );
}

export function FormSection({ title, desc, children }: { title: string; desc?: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-6 border-b border-border pb-8 last:border-0 last:pb-0 md:grid-cols-[1fr_2fr]">
      <div>
        <h3 className="font-display text-sm font-semibold text-foreground">{title}</h3>
        {desc && <p className="mt-1 text-xs text-muted-foreground">{desc}</p>}
      </div>
      <div>{children}</div>
    </div>
  );
}

