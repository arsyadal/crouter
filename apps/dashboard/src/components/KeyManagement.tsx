"use client";

import React, { useState } from "react";
import { KeyItem, KeyCreateResult, createKey, revokeKey } from "@/lib/api";
import {
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
  RefreshCw,
  Ban,
  ShieldCheck,
  AlertTriangle,
  X,
  ExternalLink,
  Info,
} from "lucide-react";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

interface KeyManagementProps {
  keys: KeyItem[];
  loading: boolean;
  onRefresh: () => void;
  onKeySelectedForPlayground?: (key: string) => void;
}

export function KeyManagement({
  keys,
  loading,
  onRefresh,
  onKeySelectedForPlayground,
}: KeyManagementProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [tenantInput, setTenantInput] = useState("");
  const [rateLimitInput, setRateLimitInput] = useState(60);
  const [concurrencyInput, setConcurrencyInput] = useState(10);
  const [explicitKeyInput, setExplicitKeyInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New key created popup
  const [createdResult, setCreatedResult] = useState<KeyCreateResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Revoke state
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tenantInput.trim()) {
      setError("Tenant name is required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const result = await createKey({
        tenant: tenantInput.trim(),
        rate_limit_rpm: Number(rateLimitInput),
        max_concurrency: Number(concurrencyInput),
        key: explicitKeyInput.trim() || undefined,
      });
      setCreatedResult(result);
      setModalOpen(false);
      setTenantInput("");
      setExplicitKeyInput("");
      onRefresh();
    } catch (err: any) {
      setError(err.message || "Failed to create API key");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevokeKey = async (id: string) => {
    if (!confirm("Are you sure you want to revoke this API key? This action is irreversible.")) {
      return;
    }
    setRevokingId(id);
    try {
      await revokeKey(id);
      onRefresh();
    } catch (err: any) {
      alert(err.message || "Failed to revoke key");
    } finally {
      setRevokingId(null);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header and Create Button */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
            Gateway API Key Governance
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Issue tenant-scoped bearer keys backed by SHA-256 hash persistence, Redis rate limits, and concurrency caps.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 shadow-sm transition dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => {
              setModalOpen(true);
              setError(null);
            }}
            className="inline-flex items-center space-x-1.5 rounded-md bg-zinc-900 px-3.5 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-zinc-800 transition dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Create API Key</span>
          </button>
        </div>
      </div>

      {/* Keys Table */}
      <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/40">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-zinc-700 dark:text-zinc-300">
            <thead className="border-b border-zinc-200 bg-zinc-50 uppercase tracking-wider text-zinc-500 font-medium text-[11px] dark:border-zinc-800 dark:bg-zinc-950/70 dark:text-zinc-400">
              <tr>
                <th className="px-5 py-3 font-medium">Tenant</th>
                <th className="px-5 py-3 font-medium">Key Prefix</th>
                <th className="px-5 py-3 font-medium">Rate Limit</th>
                <th className="px-5 py-3 font-medium">Concurrency</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Created</th>
                <th className="px-5 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200/80 dark:divide-zinc-800/60">
              {keys.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-zinc-400 dark:text-zinc-500">
                    No gateway keys found. Click &quot;Create API Key&quot; to issue the first token.
                  </td>
                </tr>
              ) : (
                keys.map((k) => (
                  <tr key={k.id} className="transition hover:bg-zinc-50 dark:hover:bg-zinc-800/30">
                    <td className="px-5 py-3 font-medium text-zinc-900 dark:text-zinc-100">
                      {k.tenant}
                    </td>
                    <td className="px-5 py-3 font-mono text-zinc-700 dark:text-zinc-300">
                      {k.key_prefix}...
                    </td>
                    <td className="px-5 py-3">
                      <span className="rounded-full border border-zinc-200 bg-zinc-100 px-2.5 py-0.5 font-mono text-zinc-700 text-[11px] dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300">
                        {k.rate_limit_rpm} RPM
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className="rounded-full border border-zinc-200 bg-zinc-100 px-2.5 py-0.5 font-mono text-zinc-700 text-[11px] dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300">
                        {k.max_concurrency} inflight
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {k.is_active ? (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 text-xs font-semibold dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
                          <ShieldCheck className="h-3 w-3" />
                          <span>ACTIVE</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-600 border border-zinc-200 dark:bg-zinc-800/80 dark:text-zinc-400 dark:border-zinc-700">
                          <Ban className="h-3 w-3" />
                          <span>REVOKED</span>
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-zinc-500 dark:text-zinc-400 font-mono text-[11px]">
                      {k.created_at ? new Date(k.created_at).toLocaleString() : "-"}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {k.is_active && (
                        <button
                          onClick={() => handleRevokeKey(k.id)}
                          disabled={revokingId === k.id}
                          className="inline-flex items-center space-x-1 rounded-md border border-rose-200 bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-700 hover:bg-rose-100 transition dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-400 dark:hover:bg-rose-900/40 disabled:opacity-50"
                        >
                          <Ban className="h-3 w-3" />
                          <span>Revoke</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Creation Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center space-x-2">
                <div className="rounded-md bg-zinc-100 p-1 border border-zinc-200 dark:bg-zinc-800 dark:border-zinc-700/50">
                  <Key className="h-4 w-4 text-zinc-700 dark:text-zinc-300" />
                </div>
                <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Create New Gateway API Key</h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateKey} className="mt-4 space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Validation Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
                  Tenant Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. sdcraft, dev-team, agent-service"
                  value={tenantInput}
                  onChange={(e) => setTenantInput(e.target.value)}
                  className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
                    Rate Limit (RPM)
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={rateLimitInput}
                    onChange={(e) => setRateLimitInput(Number(e.target.value))}
                    className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:border-zinc-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
                    Max Concurrency
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={concurrencyInput}
                    onChange={(e) => setConcurrencyInput(Number(e.target.value))}
                    className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:border-zinc-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
                  Explicit Key Token (Optional)
                </label>
                <input
                  type="text"
                  placeholder="Leave empty to auto-generate cr_live_..."
                  value={explicitKeyInput}
                  onChange={(e) => setExplicitKeyInput(e.target.value)}
                  className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs font-mono text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-500"
                />
              </div>

              <div className="mt-6 flex justify-end space-x-2 pt-3 border-t border-zinc-200 dark:border-zinc-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-md border border-zinc-200 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 transition dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-md bg-zinc-900 px-3.5 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 disabled:opacity-50"
                >
                  {submitting ? "Generating..." : "Generate Key"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Key Created Modal (Raw Key Display) */}
      {createdResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center space-x-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/30">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">API Key Created Successfully</h3>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Tenant: {createdResult.tenant}</p>
              </div>
            </div>

            <div className="mt-4">
              <Alert variant="warning">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Save this key now</AlertTitle>
                <AlertDescription>
                  For security, only the SHA-256 hash is saved in CRouter database. You will not be able to view this raw token again.
                </AlertDescription>
              </Alert>
            </div>

            <div className="mt-4">
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">Generated Bearer Token</label>
              <div className="mt-1 flex items-center space-x-2">
                <input
                  type="text"
                  readOnly
                  value={createdResult.key}
                  className="w-full rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs font-mono text-zinc-900 selection:bg-zinc-200 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-200 focus:outline-none"
                />
                <button
                  onClick={() => handleCopy(createdResult.key)}
                  className="inline-flex items-center space-x-1 rounded-md bg-zinc-900 px-3 py-2 text-xs font-medium text-white transition hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 shrink-0"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copied ? "Copied" : "Copy"}</span>
                </button>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-2 pt-4 border-t border-zinc-200 dark:border-zinc-800">
              {onKeySelectedForPlayground && (
                <button
                  onClick={() => {
                    onKeySelectedForPlayground(createdResult.key);
                    setCreatedResult(null);
                  }}
                  className="rounded-md border border-zinc-300 bg-zinc-100 px-3.5 py-1.5 text-xs font-medium text-zinc-800 hover:bg-zinc-200 transition dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
                >
                  Use in Playground
                </button>
              )}
              <button
                onClick={() => setCreatedResult(null)}
                className="rounded-md border border-zinc-200 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 transition dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
