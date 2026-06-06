import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { StatusBadge } from "@/components/Badge";
import { Button, LinkButton } from "@/components/Button";
import { vendorAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/vendors/")({ component: VendorsPage });

function VendorsPage() {
  const nav = useNavigate();
  const [vendors, setVendors] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    loadVendors();
    loadCategories();
  }, []);

  const loadVendors = async () => {
    try {
      setIsLoading(true);
      const data = await vendorAPI.list({
        search: q || undefined,
        status: statusFilter || undefined,
        categoryId: cat || undefined,
      });
      setVendors(data.items || []);
    } catch (err: any) {
      console.error('Failed to load vendors:', err);
      setError(err.message || 'Failed to load vendors');
    } finally {
      setIsLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await vendorAPI.getCategories();
      setCategories(data || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  // Reload when filters change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!isLoading) loadVendors();
    }, 300); // Debounce search
    return () => clearTimeout(timer);
  }, [q, cat, statusFilter]);

  if (isLoading && vendors.length === 0) {
    return (
      <Layout>
        <PageHeader
          title="Vendor Management"
          breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Vendors" }]}
        />
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="animate-spin h-8 w-8 text-gray-400" />
        </div>
      </Layout>
    );
  }

  if (error && vendors.length === 0) {
    return (
      <Layout>
        <PageHeader
          title="Vendor Management"
          breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Vendors" }]}
        />
        <div className="rounded-md bg-red-50 border border-red-200 p-4">
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={loadVendors}
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
        title="Vendor Management"
        breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Vendors" }]}
        actions={<Button onClick={() => nav({ to: "/vendors/add" })}>+ Add Vendor</Button>}
      />
      <div className="mb-4 flex flex-wrap gap-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search vendors…"
          className="w-72 rounded-md border border-border bg-background px-3 py-2 text-sm"
        />
        <select
          value={cat}
          onChange={(e) => setCat(e.target.value)}
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
      
      {isLoading && (
        <div className="mb-2 text-sm text-muted-foreground flex items-center gap-2">
          <Loader2 className="animate-spin h-4 w-4" />
          Loading...
        </div>
      )}
      
      <DataTable
        columns={["Vendor Name", "Category", "GST Number", "Contact", "Status", "Actions"]}
        empty={vendors.length === 0}
      >
        {vendors.map((v) => (
          <Tr key={v.id}>
            <Td>
              <div className="font-medium">{v.name}</div>
              {v.rating && <div className="text-xs text-muted-foreground">★ {v.rating}</div>}
            </Td>
            <Td>{v.categoryName || (v.category && v.category.name) || '-'}</Td>
            <Td className="font-mono text-xs">{v.gstNumber}</Td>
            <Td>
              <div>{v.email}</div>
              {v.phone && <div className="text-xs text-muted-foreground">{v.phone}</div>}
            </Td>
            <Td><StatusBadge status={v.status} /></Td>
            <Td>
              <div className="flex gap-2">
                <LinkButton to={`/vendors/${v.id}`} variant="ghost">View</LinkButton>
              </div>
            </Td>
          </Tr>
        ))}
      </DataTable>
    </Layout>
  );
}
