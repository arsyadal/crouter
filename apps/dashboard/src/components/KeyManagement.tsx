"use client";

import React, { useState } from "react";
import { KeyItem, KeyCreateResult, createKey, revokeKey } from "@/lib/api";
import {
  Key,
  Plus,
  Copy,
  Check,
  Ban,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  X,
} from "lucide-react";

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
          <h2 className="text-xl font-bold tracking-tight text-white">
            Gateway API Key Governance
          </h2>
          <p className="text-sm text-slate-400">
            Issue tenant-scoped bearer keys backed by SHA-256 hash persistence, Redis rate limits, and concurrency caps.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center space-x-2 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs font-medium text-slate-200 transition hover:bg-slate-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => {
              setModalOpen(true);
              setError(null);
            }}
            className="inline-flex items-center space-x-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500"
          >
            <Plus className="h-4 w-4" />
            <span>Create API Key</span>
          </button>
        </div>
      </div>

      {/* Keys Table */}
      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/40 uppercase tracking-wider text-slate-400">
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
            <tbody className="divide-y divide-slate-800/60">
              {keys.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-slate-500">
                    No gateway keys found. Click &quot;Create API Key&quot; to issue the first token.
                  </td>
                </tr>
              ) : (
                keys.map((k) => (
                  <tr key={k.id} className="transition hover:bg-slate-800/30">
                    <td className="px-5 py-3 font-medium text-white">
                      {k.tenant}
                    </td>
                    <td className="px-5 py-3 font-mono text-slate-300">
                      {k.key_prefix}...
                    </td>
                    <td className="px-5 py-3">
                      <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-300">
                        {k.rate_limit_rpm} RPM
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-300">
                        {k.max_concurrency} inflight
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {k.is_active ? (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                          <ShieldCheck className="h-3 w-3" />
                          <span>ACTIVE</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-semibold text-slate-400 border border-slate-700">
                          <Ban className="h-3 w-3" />
                          <span>REVOKED</span>
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-slate-400">
                      {k.created_at ? new Date(k.created_at).toLocaleString() : "-"}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {k.is_active && (
                        <button
                          onClick={() => handleRevokeKey(k.id)}
                          disabled={revokingId === k.id}
                          className="inline-flex items-center space-x-1 rounded border border-rose-800/60 bg-rose-950/40 px-2.5 py-1 text-xs font-medium text-rose-300 transition hover:bg-rose-900/60 disabled:opacity-50"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-[#0f172a] p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Key className="h-5 w-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Create New Gateway API Key</h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateKey} className="mt-4 space-y-4">
              {error && (
                <div className="rounded-lg bg-rose-950/40 p-3 text-xs text-rose-300 border border-rose-800/60">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-300">
                  Tenant Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. sdcraft, dev-team, agent-service"
                  value={tenantInput}
                  onChange={(e) => setTenantInput(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300">
                    Rate Limit (RPM)
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={rateLimitInput}
                    onChange={(e) => setRateLimitInput(Number(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">
                    Max Concurrency
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={concurrencyInput}
                    onChange={(e) => setConcurrencyInput(Number(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300">
                  Explicit Key Token (Optional)
                </label>
                <input
                  type="text"
                  placeholder="Leave empty to auto-generate cr_live_..."
                  value={explicitKeyInput}
                  onChange={(e) => setExplicitKeyInput(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-mono text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="mt-6 flex justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-indigo-500/40 bg-[#0f172a] p-6 shadow-2xl">
            <div className="flex items-center space-x-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">API Key Created Successfully!</h3>
                <p className="text-xs text-slate-400">Tenant: {createdResult.tenant}</p>
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-950/20 p-3 text-xs text-amber-300 flex items-start space-x-2">
              <AlertTriangle className="h-5 w-5 shrink-0 text-amber-400" />
              <span>
                <strong>Save this key now!</strong> For security, only the SHA-256 hash is saved in CRouter database. You will not be able to view this raw token again.
              </span>
            </div>

            <div className="mt-4">
              <label className="block text-xs font-medium text-slate-300">Generated Bearer Token</label>
              <div className="mt-1 flex items-center space-x-2">
                <input
                  type="text"
                  readOnly
                  value={createdResult.key}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-mono text-indigo-300 selection:bg-indigo-500 selection:text-white"
                />
                <button
                  onClick={() => handleCopy(createdResult.key)}
                  className="inline-flex items-center space-x-1 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-indigo-500"
                >
                  {copied ? <Check className="h-4 w-4 text-emerald-300" /> : <Copy className="h-4 w-4" />}
                  <span>{copied ? "Copied" : "Copy"}</span>
                </button>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3 pt-4 border-t border-slate-800">
              {onKeySelectedForPlayground && (
                <button
                  onClick={() => {
                    onKeySelectedForPlayground(createdResult.key);
                    setCreatedResult(null);
                  }}
                  className="rounded-lg border border-indigo-500/40 bg-indigo-950/40 px-4 py-2 text-xs font-medium text-indigo-300 hover:bg-indigo-900/60"
                >
                  Use in Playground
                </button>
              )}
              <button
                onClick={() => setCreatedResult(null)}
                className="rounded-lg bg-slate-800 px-4 py-2 text-xs font-medium text-white hover:bg-slate-700"
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
