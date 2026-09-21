"use client";

import React, { useState } from "react";
import { PolicyDetail, resetBreaker, tripBreaker } from "@/lib/api";
import {
  RotateCcw,
  ZapOff,
  CheckCircle2,
  AlertOctagon,
  HelpCircle,
  RefreshCw,
  GitFork,
  Clock,
  ShieldAlert,
} from "lucide-react";

interface RouteMonitoringProps {
  policies: PolicyDetail[];
  loading: boolean;
  onRefresh: () => void;
}

export function RouteMonitoring({
  policies,
  loading,
  onRefresh,
}: RouteMonitoringProps) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const handleReset = async (routeKey: string) => {
    setActionLoading(routeKey);
    setMessage(null);
    try {
      const res = await resetBreaker(routeKey);
      setMessage({ text: res.message, type: "success" });
      onRefresh();
    } catch (e: any) {
      setMessage({ text: e.message || "Failed to reset breaker", type: "error" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleTrip = async (routeKey: string) => {
    setActionLoading(routeKey);
    setMessage(null);
    try {
      const res = await tripBreaker(routeKey);
      setMessage({ text: res.message, type: "success" });
      onRefresh();
    } catch (e: any) {
      setMessage({ text: e.message || "Failed to trip breaker", type: "error" });
    } finally {
      setActionLoading(null);
    }
  };

  const getBreakerBadge = (state: string) => {
    switch (state) {
      case "CLOSED":
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>CLOSED (Healthy)</span>
          </span>
        );
      case "OPEN":
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-rose-500/15 px-2.5 py-0.5 text-xs font-semibold text-rose-400 border border-rose-500/30 animate-pulse">
            <AlertOctagon className="h-3.5 w-3.5" />
            <span>OPEN (Tripped)</span>
          </span>
        );
      case "HALF_OPEN":
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-400 border border-amber-500/20">
            <HelpCircle className="h-3.5 w-3.5" />
            <span>HALF-OPEN (Canary)</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-300">
            <span>{state}</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">
            Routing Policies & Circuit Breakers
          </h2>
          <p className="text-sm text-slate-400">
            Monitor active model aliases, provider priority chains, and circuit breaker trip mechanics.
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center space-x-2 rounded-lg border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-xs font-medium text-slate-200 transition hover:bg-slate-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh States</span>
        </button>
      </div>

      {/* Action Notification */}
      {message && (
        <div
          className={`rounded-lg p-3 text-xs border ${
            message.type === "success"
              ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/60"
              : "bg-rose-950/40 text-rose-300 border-rose-800/60"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Policies List */}
      <div className="space-y-4">
        {policies.map((policy) => (
          <div
            key={policy.id}
            className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40 shadow-sm"
          >
            {/* Policy Title Banner */}
            <div className="flex flex-col justify-between border-b border-slate-800 bg-slate-900/70 px-5 py-3.5 sm:flex-row sm:items-center">
              <div className="flex items-center space-x-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <GitFork className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-base font-bold text-white">
                      {policy.alias}
                    </span>
                    <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] text-slate-300">
                      max_retries: {policy.max_retries}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    {policy.description || "Inference routing fallback policy"}
                  </p>
                </div>
              </div>
              <div className="mt-2 flex items-center space-x-2 text-xs text-slate-400 sm:mt-0">
                <Clock className="h-3.5 w-3.5 text-slate-500" />
                <span>Timeout: {policy.timeout_ms}ms</span>
              </div>
            </div>

            {/* Routes Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="border-b border-slate-800 bg-slate-950/40 uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-5 py-3 font-medium">Priority</th>
                    <th className="px-5 py-3 font-medium">Provider</th>
                    <th className="px-5 py-3 font-medium">Upstream Model</th>
                    <th className="px-5 py-3 font-medium">Route Key</th>
                    <th className="px-5 py-3 font-medium">Breaker State</th>
                    <th className="px-5 py-3 text-right font-medium">Breaker Simulation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {policy.routes.map((route) => {
                    const isBusy = actionLoading === route.route_key;
                    return (
                      <tr
                        key={route.id}
                        className="transition hover:bg-slate-800/30"
                      >
                        <td className="px-5 py-3 font-mono font-medium">
                          <span
                            className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                              route.priority === 1
                                ? "bg-indigo-600 text-white shadow-sm"
                                : route.priority === 2
                                ? "bg-slate-700 text-slate-200"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            P{route.priority}
                          </span>
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-white">
                              {route.provider_name}
                            </span>
                            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400 uppercase">
                              {route.provider_type}
                            </span>
                          </div>
                        </td>
                        <td className="px-5 py-3 font-mono text-slate-300">
                          {route.upstream_model}
                        </td>
                        <td className="px-5 py-3 font-mono text-slate-400 text-[11px]">
                          {route.route_key}
                        </td>
                        <td className="px-5 py-3">
                          {getBreakerBadge(route.breaker_state)}
                        </td>
                        <td className="px-5 py-3 text-right">
                          <div className="flex items-center justify-end space-x-2">
                            {route.breaker_state === "OPEN" ? (
                              <button
                                onClick={() => handleReset(route.route_key)}
                                disabled={isBusy}
                                className="inline-flex items-center space-x-1 rounded bg-emerald-600/80 px-2.5 py-1 text-xs font-medium text-white transition hover:bg-emerald-600 disabled:opacity-50"
                              >
                                <RotateCcw className="h-3 w-3" />
                                <span>Reset Breaker</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => handleTrip(route.route_key)}
                                disabled={isBusy}
                                className="inline-flex items-center space-x-1 rounded border border-rose-800/60 bg-rose-950/40 px-2.5 py-1 text-xs font-medium text-rose-300 transition hover:bg-rose-900/60 disabled:opacity-50"
                              >
                                <ZapOff className="h-3 w-3" />
                                <span>Simulate Trip</span>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
