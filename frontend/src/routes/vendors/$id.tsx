import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { StatusBadge } from "@/components/Badge";
import { Button, LinkButton } from "@/components/Button";
import { vendorAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/vendors/$id")({ component: VendorDetailPage });

function VendorDetailPage() {
  const { id } = Route.useParams();
  const nav = useNavigate();
  const [vendor, setVendor] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    vendorAPI.getById(id).then(setVendor).catch(console.error).finally(() => setIsLoading(false));
  }, [id]);

  if (isLoading) {
    return <Layout><div className="flex items-center justify-center min-h-[300px]"><Loader2 className="animate-spin h-8 w-8 text-gray-400" /></div></Layout>;
  }
  if (!vendor) {
    return <Layout><div className="p-8 text-center text-muted-foreground">Vendor not found.</div></Layout>;
  }

  return (
    <Layout>
      <PageHeader title={vendor.name} breadcrumb={[{ label: "Vendors", to: "/vendors" }, { label: vendor.name }]}
        actions={<LinkButton to={`/vendors/edit/${id}`}>Edit Vendor</LinkButton>}
      />
      <div className="rounded-lg border border-border bg-card p-6">
        <dl className="grid gap-4 sm:grid-cols-2">
          <div><dt className="text-xs text-muted-foreground">Vendor Name</dt><dd className="mt-1 font-medium">{vendor.name}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Status</dt><dd className="mt-1"><StatusBadge status={vendor.status} /></dd></div>
          <div><dt className="text-xs text-muted-foreground">GST Number</dt><dd className="mt-1 font-mono">{vendor.gstNumber}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Category</dt><dd className="mt-1">{vendor.category?.name || "-"}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Email</dt><dd className="mt-1">{vendor.email}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Phone</dt><dd className="mt-1">{vendor.phone || "-"}</dd></div>
          <div className="sm:col-span-2"><dt className="text-xs text-muted-foreground">Address</dt><dd className="mt-1">{vendor.address || "-"}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Created</dt><dd className="mt-1 text-sm text-muted-foreground">{vendor.createdAt ? new Date(vendor.createdAt).toLocaleDateString() : "-"}</dd></div>
        </dl>
      </div>
    </Layout>
  );
}
