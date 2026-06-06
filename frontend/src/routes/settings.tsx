import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Layout, PageHeader } from "@/components/Layout";
import { DataTable, Td, Tr } from "@/components/Table";
import { StatusBadge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { inputCls } from "@/components/AuthShell";
import { api } from "@/lib/api/client";
import { vendorAPI } from "@/lib/api/endpoints";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/settings")({ component: SettingsPage });

function SettingsPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [newCat, setNewCat] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Load users from the database via a direct API call
      // We'll use the vendors endpoint pattern - but for users we need admin endpoint
      // For now, load from activity logs users or just show current known users
      const vendorsData = await vendorAPI.list({ page: 1 });
      const catsData = await vendorAPI.getCategories();
      setCategories(catsData || []);
      
      // Load users - we don't have a user list endpoint yet, so fetch from DB directly
      // Use a workaround: the backend doesn't have GET /api/users yet
      // Show at least the current user info
      const me = await api.get<any>("/api/users/me");
      setUsers([{
        id: me.id,
        name: me.username || me.email,
        email: me.email,
        role: me.role,
        status: me.is_active ? "Active" : "Inactive",
        isActive: me.is_active,
      }]);
    } catch (err) {
      console.error("Failed to load settings data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCategory = async () => {
    if (!newCat.trim()) return;
    try {
      await vendorAPI.createCategory(newCat.trim());
      setNewCat("");
      // Reload categories
      const catsData = await vendorAPI.getCategories();
      setCategories(catsData || []);
    } catch (err: any) {
      alert(err.message || "Failed to create category");
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <PageHeader title="Admin Settings" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Settings" }]} />
        <div className="flex items-center justify-center min-h-[300px]">
          <Loader2 className="animate-spin h-8 w-8 text-gray-400" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <PageHeader title="Admin Settings" breadcrumb={[{ label: "Workspace", to: "/dashboard" }, { label: "Settings" }]} />
      <section className="mb-8">
        <h2 className="mb-3 font-display text-base font-semibold">User Management</h2>
        <DataTable columns={["Name", "Email", "Role", "Status"]}>
          {users.map((u, i) => (
            <Tr key={i}>
              <Td className="font-medium">{u.name}</Td>
              <Td className="text-muted-foreground">{u.email}</Td>
              <Td>{u.role}</Td>
              <Td><StatusBadge status={u.status} /></Td>
            </Tr>
          ))}
        </DataTable>
        <p className="mt-2 text-xs text-muted-foreground">User management requires a dedicated admin API endpoint (coming soon).</p>
      </section>

      <section>
        <h2 className="mb-3 font-display text-base font-semibold">Vendor Categories</h2>
        <div className="rounded-lg border border-border bg-card p-6">
          <ul className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-3">
            {categories.map((c: any) => (
              <li key={c.id || c.name} className="flex items-center justify-between rounded-md border border-border bg-background px-3 py-2 text-sm">
                <span>{c.name || c}</span>
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            <input value={newCat} onChange={(e) => setNewCat(e.target.value)} placeholder="New category name..." className={inputCls + " max-w-sm"} onKeyDown={(e) => e.key === "Enter" && handleAddCategory()} />
            <Button onClick={handleAddCategory}>Add Category</Button>
          </div>
        </div>
      </section>
    </Layout>
  );
}
