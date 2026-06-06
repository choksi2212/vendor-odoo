import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthShell, Field, inputCls } from "@/components/AuthShell";
import { useAuth } from "@/context/AuthContext";
import { Eye, EyeOff, Loader2 } from "lucide-react";

export const Route = createFileRoute("/login")({ component: LoginPage });

function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [pwd, setPwd] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const result = await login(email, pwd);
      
      if (result.requires2FA) {
        // Redirect to OTP verification page
        nav({ to: "/verify-otp", search: { pendingToken: result.pendingToken } });
      } else {
        // Login successful, redirect to dashboard
        nav({ to: "/dashboard" });
      }
    } catch (err: any) {
      setError(err.message || "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthShell>
      <h1 className="font-display text-2xl font-semibold text-foreground">Welcome back</h1>
      <p className="mt-1 text-sm text-muted-foreground">Sign in to your VendorBridge workspace.</p>
      
      <form onSubmit={handleLogin} className="mt-8 space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800">
            {error}
          </div>
        )}
        
        <Field label="Email">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCls}
            placeholder="you@example.com"
            required
            disabled={isLoading}
          />
        </Field>
        
        <Field label="Password">
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              value={pwd}
              onChange={(e) => setPwd(e.target.value)}
              className={inputCls}
              placeholder="Enter your password"
              required
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
        
        <div className="flex items-center justify-between text-xs">
          <label className="flex items-center gap-2 text-muted-foreground">
            <input type="checkbox" defaultChecked disabled={isLoading} /> Remember me
          </label>
          <Link
            to="/forgot-password"
            className="font-medium text-[color:var(--action)] hover:underline"
          >
            Forgot password?
          </Link>
        </div>
        
        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-md bg-[color:var(--action)] px-4 py-2.5 text-sm font-medium text-[color:var(--action-foreground)] hover:bg-[color:var(--action)]/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading && <Loader2 size={16} className="animate-spin" />}
          {isLoading ? "Signing in..." : "Sign in"}
        </button>
        
        <p className="text-center text-xs text-muted-foreground">
          New to VendorBridge? <Link to="/signup" className="font-medium text-[color:var(--action)] hover:underline">Create an account</Link>
        </p>
      </form>
    </AuthShell>
  );
}
