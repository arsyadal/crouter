"use client";

import React, { useState } from "react";
import { KeyRound, Lock, Eye, EyeOff, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, X } from "lucide-react";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (token: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanToken = token.trim();

    if (!cleanToken) {
      setError("Please enter a valid master key or administration token.");
      return;
    }

    setIsVerifying(true);
    setError(null);

    // Simulate instant local verification or gateway token check
    setTimeout(() => {
      setIsVerifying(false);
      // Persist auth in localStorage for session preservation
      if (typeof window !== "undefined") {
        localStorage.setItem(
          "crouter_auth",
          JSON.stringify({
            authenticated: true,
            tenant: cleanToken === "crouter-admin-2026" ? "Master Admin" : "Gateway Operator",
            timestamp: Date.now(),
          })
        );
      }
      onSuccess(cleanToken);
    }, 350);
  };

  const handleUseDevToken = () => {
    setToken("crouter-admin-2026");
    setError(null);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900 transition-all">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close authentication modal"
          className="absolute right-4 top-4 rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100">
            <Lock className="h-5 w-5" />
          </div>
          <div>
            <h3 id="auth-modal-title" className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
              Gateway Console Access
            </h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Admin authentication required to manage keys and view live routes.
            </p>
          </div>
        </div>

        {/* Error Alert using Shadcn Alert */}
        {error && (
          <div className="mt-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              <AlertTitle>Authentication Failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label
              htmlFor="auth-token-input"
              className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300"
            >
              Master Key or Admin Token
            </label>
            <div className="relative mt-1.5">
              <input
                id="auth-token-input"
                type={showToken ? "text" : "password"}
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Enter master key (e.g. crouter-admin-2026)"
                className="w-full rounded-xl border border-zinc-300 bg-zinc-50 px-3.5 py-2.5 pr-11 text-xs font-mono text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900/10 dark:border-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-zinc-400 dark:focus:ring-zinc-400/20"
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1.5 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                aria-label={showToken ? "Hide token" : "Show token"}
              >
                {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Quick Dev Token Helper */}
          <div className="flex items-center justify-between rounded-lg border border-dashed border-zinc-200 bg-zinc-50/50 p-2.5 dark:border-zinc-800 dark:bg-zinc-950/40">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              <span className="text-[11px] text-zinc-600 dark:text-zinc-400">
                Local dev default: <code className="font-mono text-zinc-800 dark:text-zinc-200">crouter-admin-2026</code>
              </span>
            </div>
            <button
              type="button"
              onClick={handleUseDevToken}
              className="rounded-md bg-zinc-200/80 px-2 py-1 text-[10px] font-semibold text-zinc-800 hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 transition"
            >
              Autofill
            </button>
          </div>

          <div className="mt-6 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="min-h-[44px] rounded-xl border border-zinc-300 bg-white px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-750 transition"
            >
              Back to Landing
            </button>
            <button
              type="submit"
              disabled={isVerifying}
              className="min-h-[44px] inline-flex items-center gap-2 rounded-xl bg-zinc-900 px-5 py-2 text-xs font-semibold text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white shadow-sm transition disabled:opacity-50"
            >
              {isVerifying ? (
                <span>Verifying...</span>
              ) : (
                <>
                  <span>Enter Console</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
