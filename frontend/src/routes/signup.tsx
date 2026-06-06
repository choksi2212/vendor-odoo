import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthShell, Field, inputCls } from "@/components/AuthShell";
import { useAuth, REVERSE_ROLE_MAP, type DisplayRole } from "@/context/AuthContext";
import { Eye, EyeOff, Loader2, CheckCircle } from "lucide-react";

export const Route = createFileRoute("/signup")({ component: SignupPage });

function SignupPage() {
  const { signup } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    pwd: "",
    confirm: "",
    role: "Procurement Officer" as DisplayRole
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const u = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  const validatePassword = (pwd: string): string | null => {
    if (pwd.length < 8) return "Password must be at least 8 characters";
    if (!/[A-Z]/.test(pwd)) return "Password must contain an uppercase letter";
    if (!/[a-z]/.test(pwd)) return "Password must contain a lowercase letter";
    if (!/[0-9]/.test(pwd)) return "Password must contain a digit";
    if (!/[@$!%*?&#^()_\-+=\[\]{}]/.test(pwd)) return "Password must contain a special character";
    return null;
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Validation
    if (form.pwd !== form.confirm) {
      setError("Passwords do not match");
      return;
    }

    const pwdError = validatePassword(form.pwd);
    if (pwdError) {
      setError(pwdError);
      return;
    }

    setIsLoading(true);

    try {
      // Generate username from name (lowercase, no spaces, only valid chars)
      const username = form.name.toLowerCase().replace(/[^a-z0-9_]/g, '_').replace(/_+/g, '_').slice(0, 30);
      
      await signup({
        email: form.email,
        username: username,
        password: form.pwd,
        confirmPassword: form.confirm,
        role: REVERSE_ROLE_MAP[form.role], // Convert display role to backend role
      });

      setSuccess(true);
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        nav({ to: "/login" });
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Failed to create account");
    } finally {
      setIsLoading(false);
    }
  }

  if (success) {
    return (
      <AuthShell>
        <div className="text-center">
          <CheckCircle className="mx-auto h-12 w-12 text-green-600" />
          <h1 className="mt-4 font-display text-2xl font-semibold text-foreground">Account created!</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Redirecting you to login...
          </p>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <h1 className="font-display text-2xl font-semibold text-foreground">Create your account</h1>
      <p className="mt-1 text-sm text-muted-foreground">Set up your VendorBridge workspace in seconds.</p>
      
      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800">
            {error}
          </div>
        )}
        
        <Field label="Full name">
          <input
            className={inputCls}
            required
            value={form.name}
            onChange={u("name")}
            placeholder="Jane Smith"
            disabled={isLoading}
          />
        </Field>
        
        <Field label="Work email">
          <input
            type="email"
            className={inputCls}
            required
            value={form.email}
            onChange={u("email")}
            placeholder="jane@company.com"
            disabled={isLoading}
          />
        </Field>
        
        <div className="grid grid-cols-2 gap-3">
          <Field label="Password">
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                className={inputCls}
                required
                value={form.pwd}
                onChange={u("pwd")}
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </Field>
          
          <Field label="Confirm password">
            <div className="relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                className={inputCls}
                required
                value={form.confirm}
                onChange={u("confirm")}
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                tabIndex={-1}
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </Field>
        </div>
        
        <Field label="Role">
          <select className={inputCls} value={form.role} onChange={u("role")} disabled={isLoading}>
            <option>Procurement Officer</option>
            <option>Vendor</option>
            <option>Manager / Approver</option>
            <option>Admin</option>
          </select>
        </Field>
        
        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-md bg-[color:var(--action)] px-4 py-2.5 text-sm font-medium text-[color:var(--action-foreground)] hover:bg-[color:var(--action)]/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading && <Loader2 size={16} className="animate-spin" />}
          {isLoading ? "Creating account..." : "Create account"}
        </button>
        
        <p className="text-center text-xs text-muted-foreground">
          Already have an account? <Link to="/login" className="font-medium text-[color:var(--action)] hover:underline">Sign in</Link>
        </p>
      </form>
    </AuthShell>
  );
}
