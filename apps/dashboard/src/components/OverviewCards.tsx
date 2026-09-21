"use client";

import React from "react";
import { OverviewData } from "@/lib/api";
import { Layers, Zap, Key, Radio, CheckCircle2, AlertTriangle } from "lucide-react";

interface OverviewCardsProps {
  overview: OverviewData | null;
  loading: boolean;
}

export function OverviewCards({ overview, loading }: OverviewCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {/* 1. Model Routes */}
      <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 shadow-sm backdrop-blur">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Active Model Routes
          </span>
          <div className="rounded-lg bg-indigo-500/10 p-2 text-indigo-400 border border-indigo-500/20">
            <Layers className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-white">
            {loading ? "..." : overview?.total_policies ?? 0}
          </span>
          <span className="text-xs text-slate-400">
            ({overview?.total_routes ?? 0} fallback hops)
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          `auto/coding`, `fast/chat`, etc.
        </p>
      </div>

      {/* 2. Circuit Breakers */}
      <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 shadow-sm backdrop-blur">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Circuit Breaker Status
          </span>
          <div
            className={`rounded-lg p-2 border ${
              (overview?.open_breakers_count ?? 0) > 0
                ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            }`}
          >
            <Zap className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span
            className={`text-2xl font-bold ${
              (overview?.open_breakers_count ?? 0) > 0
                ? "text-rose-400"
                : "text-emerald-400"
            }`}
          >
            {loading
              ? "..."
              : (overview?.open_breakers_count ?? 0) > 0
              ? `${overview?.open_breakers_count} Tripped`
              : "All Healthy"}
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          Auto-trips on 5 consecutive 5xx/timeouts
        </p>
      </div>

      {/* 3. API Keys */}
      <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 shadow-sm backdrop-blur">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Authenticated Keys
          </span>
          <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400 border border-cyan-500/20">
            <Key className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-white">
            {loading ? "..." : overview?.active_keys ?? 0}
          </span>
          <span className="text-xs text-slate-400">
            active / {overview?.total_keys ?? 0} total
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          SHA-256 hashed with RPM limits
        </p>
      </div>

      {/* 4. Live Providers Status */}
      <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 shadow-sm backdrop-blur">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Provider Mode
          </span>
          <div className="rounded-lg bg-amber-500/10 p-2 text-amber-400 border border-amber-500/20">
            <Radio className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex flex-col space-y-1">
          <div className="flex items-center space-x-1.5 text-xs">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                overview?.live_gemini_configured
                  ? "bg-emerald-400"
                  : "bg-slate-600"
              }`}
            />
            <span
              className={
                overview?.live_gemini_configured
                  ? "text-emerald-300 font-medium"
                  : "text-slate-400"
              }
            >
              Gemini Live: {overview?.live_gemini_configured ? "Ready" : "Rp0 Mock"}
            </span>
          </div>
          <div className="flex items-center space-x-1.5 text-xs">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                overview?.live_openrouter_configured
                  ? "bg-emerald-400"
                  : "bg-slate-600"
              }`}
            />
            <span
              className={
                overview?.live_openrouter_configured
                  ? "text-emerald-300 font-medium"
                  : "text-slate-400"
              }
            >
              OpenRouter: {overview?.live_openrouter_configured ? "Ready" : "Rp0 Mock"}
            </span>
          </div>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          {overview?.live_gemini_configured || overview?.live_openrouter_configured
            ? "Live BYOK enabled"
            : "Zero-Budget Rp0 local mock default"}
        </p>
      </div>
    </div>
  );
}
