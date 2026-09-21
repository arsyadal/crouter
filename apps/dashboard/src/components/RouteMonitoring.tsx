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
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

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
          <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 text-xs font-semibold dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>CLOSED (Healthy)</span>
          </span>
        );
      case "OPEN":
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200 px-2.5 py-0.5 text-xs font-semibold animate-pulse dark:bg-rose-500/15 dark:text-rose-400 dark:border-rose-500/30">
            <AlertOctagon className="h-3.5 w-3.5" />
            <span>OPEN (Tripped)</span>
          </span>
        );
      case "HALF_OPEN":
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 text-xs font-semibold dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20">
            <HelpCircle className="h-3.5 w-3.5" />
            <span>HALF-OPEN (Canary)</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-750">
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
          <h2 className="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
            Routing Policies & Circuit Breakers
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Monitor active model aliases, provider priority chains, and circuit breaker trip mechanics.
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 shadow-sm transition dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh States</span>
        </button>
      </div>

      {/* Action Notification */}
      {message && (
        <Alert variant={message.type === "success" ? "success" : "destructive"}>
          {message.type === "success" ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <AlertOctagon className="h-4 w-4" />
          )}
          <AlertTitle>{message.type === "success" ? "Circuit Breaker Updated" : "Circuit Breaker Error"}</AlertTitle>
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      {/* Policies List */}
      <div className="space-y-4">
        {policies.map((policy) => (
          <div
            key={policy.id}
            className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/40"
          >
            {/* Policy Title Banner */}
            <div className="flex flex-col justify-between border-b border-zinc-200 bg-zinc-50 px-5 py-3.5 sm:flex-row sm:items-center dark:border-zinc-800 dark:bg-zinc-900/60">
              <div className="flex items-center space-x-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 text-zinc-700 border border-zinc-200 dark:bg-zinc-800/60 dark:text-zinc-300 dark:border-zinc-700/40">
                  <GitFork className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-base font-semibold text-zinc-900 dark:text-zinc-100">
                      {policy.alias}
                    </span>
                    <span className="rounded-full bg-zinc-200/70 px-2 py-0.5 font-mono text-[10px] text-zinc-700 border border-zinc-300/60 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700">
                      max_retries: {policy.max_retries}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {policy.description || "Inference routing fallback policy"}
                  </p>
                </div>
              </div>
              <div className="mt-2 flex items-center space-x-2 text-xs text-zinc-500 font-mono dark:text-zinc-400 sm:mt-0">
                <Clock className="h-3.5 w-3.5 text-zinc-400" />
                <span>Timeout: {policy.timeout_ms}ms</span>
              </div>
            </div>

            {/* Routes Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-zinc-700 dark:text-zinc-300">
                <thead className="border-b border-zinc-200 bg-zinc-50/60 uppercase tracking-wider text-zinc-500 text-[11px] font-medium dark:border-zinc-800 dark:bg-zinc-950/70 dark:text-zinc-400">
                  <tr>
                    <th className="px-5 py-3 font-medium">Priority</th>
                    <th className="px-5 py-3 font-medium">Provider</th>
                    <th className="px-5 py-3 font-medium">Upstream Model</th>
                    <th className="px-5 py-3 font-medium">Route Key</th>
                    <th className="px-5 py-3 font-medium">Breaker State</th>
                    <th className="px-5 py-3 text-right font-medium">Breaker Simulation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/60">
                  {policy.routes.map((route) => {
                    const isBusy = actionLoading === route.route_key;
                    return (
                      <tr
                        key={route.id}
                        className="transition hover:bg-zinc-50 dark:hover:bg-zinc-800/30"
                      >
                        <td className="px-5 py-3 font-mono font-medium">
                          <span
                            className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold ${
                              route.priority === 1
                                ? "bg-zinc-900 text-white font-bold dark:bg-zinc-100 dark:text-zinc-900"
                                : "bg-zinc-100 text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700/60"
                            }`}
                          >
                            P{route.priority}
                          </span>
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                              {route.provider_name}
                            </span>
                            <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-500 uppercase border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700">
                              {route.provider_type}
                            </span>
                          </div>
                        </td>
                        <td className="px-5 py-3 font-mono text-zinc-700 text-xs dark:text-zinc-300">
                          {route.upstream_model}
                        </td>
                        <td className="px-5 py-3 font-mono text-zinc-500 text-[11px] dark:text-zinc-400">
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
                                className="inline-flex items-center space-x-1 rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100 transition dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-400 dark:hover:bg-emerald-900/40 disabled:opacity-50"
                              >
                                <RotateCcw className="h-3 w-3" />
                                <span>Reset Breaker</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => handleTrip(route.route_key)}
                                disabled={isBusy}
                                className="inline-flex items-center space-x-1 rounded-md border border-rose-200 bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-700 hover:bg-rose-100 transition dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-400 dark:hover:bg-rose-900/40 disabled:opacity-50"
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
