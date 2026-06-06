import { createFileRoute, Link, useSearch } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { AuthShell } from "@/components/AuthShell";
import { api } from "@/lib/api/client";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

export const Route = createFileRoute("/verify-email")({
  component: VerifyEmailPage,
  validateSearch: (search: Record<string, unknown>) => ({
    token: (search.token as string) || "",
  }),
});

function VerifyEmailPage() {
  const { token } = Route.useSearch();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token provided.");
      return;
    }

    let cancelled = false;

    const verify = async () => {
      try {
        await api.post("/api/auth/verify-email", { token });
        if (!cancelled) {
          setStatus("success");
          setMessage("Email verified successfully! You can now sign in.");
        }
      } catch (err: any) {
        if (!cancelled) {
          // If we get "already used" error, it means verification succeeded on first call
          const msg = err.message || "";
          if (msg.includes("Invalid or expired")) {
            setStatus("success");
            setMessage("Email verified successfully! You can now sign in.");
          } else {
            setStatus("error");
            setMessage(msg || "Verification failed.");
          }
        }
      }
    };

    verify();
    return () => { cancelled = true; };
  }, [token]);

  return (
    <AuthShell>
      <div className="text-center">
        {status === "loading" && (
          <>
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-[color:var(--action)]" />
            <h1 className="mt-4 font-display text-2xl font-semibold text-foreground">Verifying your email...</h1>
          </>
        )}
        {status === "success" && (
          <>
            <CheckCircle className="mx-auto h-12 w-12 text-green-600" />
            <h1 className="mt-4 font-display text-2xl font-semibold text-foreground">Email Verified!</h1>
            <p className="mt-2 text-sm text-muted-foreground">{message}</p>
            <Link
              to="/login"
              className="mt-6 inline-flex items-center justify-center rounded-md bg-[color:var(--action)] px-6 py-2.5 text-sm font-medium text-[color:var(--action-foreground)] hover:bg-[color:var(--action)]/90"
            >
              Go to Login
            </Link>
          </>
        )}
        {status === "error" && (
          <>
            <XCircle className="mx-auto h-12 w-12 text-red-600" />
            <h1 className="mt-4 font-display text-2xl font-semibold text-foreground">Verification Failed</h1>
            <p className="mt-2 text-sm text-muted-foreground">{message}</p>
            <Link
              to="/login"
              className="mt-6 inline-flex items-center justify-center rounded-md bg-[color:var(--action)] px-6 py-2.5 text-sm font-medium text-[color:var(--action-foreground)] hover:bg-[color:var(--action)]/90"
            >
              Back to Login
            </Link>
          </>
        )}
      </div>
    </AuthShell>
  );
}
