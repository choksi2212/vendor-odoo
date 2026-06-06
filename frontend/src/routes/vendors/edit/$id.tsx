import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { Button } from "@/components/Button";
import { inputCls } from "@/components/AuthShell";
import { vendorAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/vendors/edit/$id")({ component: VendorEditPage });

function VendorEditPage() {
  const { id } = Route.useParams();
  const nav = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", address: "", status: "" });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    vendorAPI.getById(id).then((v: any) => {
      setForm({
        name: v.name || "",
        email: v.email || "",
        phone: v.phone || "",
        address: v.address || "",
        status: v.status || "active",
      });
    }).catch(console.error).finally(() => setIsLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      await vendorAPI.update(id, form);
      nav({ to: `/vendors/${id}` });
    } catch (err: any) {
      setError(err.message || "Failed to update vendor");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <Layout><div className="flex items-center justify-center min-h-[300px]"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div></Layout>;
  }

  return (
    <Layout>
      <PageHeader title="Edit Vendor" breadcrumb={[{ label: "Vendors", to: "/vendors" }, { label: "Edit" }]} />
      <form onSubmit={handleSubmit} className="max-w-2xl rounded-lg border border-border bg-card p-6 space-y-4">
        {error && <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800">{error}</div>}
        
        <div>
          <label className="block text-xs font-medium mb-1">Vendor Name</label>
          <input className={inputCls} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium mb-1">Email</label>
            <input type="email" className={inputCls} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Phone</label>
            <input className={inputCls} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Address</label>
          <textarea className={inputCls + " h-20"} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Status</label>
          <select className={inputCls} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
        <div className="flex gap-3 pt-2">
          <Button type="submit" disabled={isSaving}>
            {isSaving && <Loader2 size={16} className="animate-spin mr-1" />}
            {isSaving ? "Saving..." : "Update Vendor"}
          </Button>
          <Button type="button" variant="ghost" onClick={() => nav({ to: "/vendors" })}>Cancel</Button>
        </div>
      </form>
    </Layout>
  );
}
