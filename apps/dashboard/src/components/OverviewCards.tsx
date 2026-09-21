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
      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm transition hover:border-zinc-300 dark:border-zinc-800/80 dark:bg-zinc-900/50 dark:hover:border-zinc-700/70">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Active Model Routes
          </span>
          <div className="rounded-md bg-zinc-100 p-1.5 text-zinc-700 border border-zinc-200 dark:bg-zinc-800/60 dark:text-zinc-300 dark:border-zinc-700/40">
            <Layers className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100 font-mono">
            {loading ? "..." : overview?.total_policies ?? 0}
          </span>
          <span className="text-xs text-zinc-500 font-mono">
            ({overview?.total_routes ?? 0} fallback hops)
          </span>
        </div>
        <p className="mt-1 text-xs text-zinc-500 font-mono">
          auto/coding, fast/chat, etc.
        </p>
      </div>

      {/* 2. Circuit Breakers */}
      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm transition hover:border-zinc-300 dark:border-zinc-800/80 dark:bg-zinc-900/50 dark:hover:border-zinc-700/70">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Circuit Breaker Status
          </span>
          <div
            className={`rounded-md p-1.5 border ${
              (overview?.open_breakers_count ?? 0) > 0
                ? "bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20"
                : "bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20"
            }`}
          >
            <Zap className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span
            className={`text-2xl font-semibold tracking-tight ${
              (overview?.open_breakers_count ?? 0) > 0
                ? "text-rose-600 dark:text-rose-400"
                : "text-emerald-600 dark:text-emerald-400"
            }`}
          >
            {loading
              ? "..."
              : (overview?.open_breakers_count ?? 0) > 0
              ? `${overview?.open_breakers_count} Tripped`
              : "All Healthy"}
          </span>
        </div>
        <p className="mt-1 text-xs text-zinc-500">
          Auto-trips on 5 consecutive 5xx/timeouts
        </p>
      </div>

      {/* 3. API Keys */}
      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm transition hover:border-zinc-300 dark:border-zinc-800/80 dark:bg-zinc-900/50 dark:hover:border-zinc-700/70">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Authenticated Keys
          </span>
          <div className="rounded-md bg-zinc-100 p-1.5 text-zinc-700 border border-zinc-200 dark:bg-zinc-800/60 dark:text-zinc-300 dark:border-zinc-700/40">
            <Key className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100 font-mono">
            {loading ? "..." : overview?.active_keys ?? 0}
          </span>
          <span className="text-xs text-zinc-500 font-mono">
            active / {overview?.total_keys ?? 0} total
          </span>
        </div>
        <p className="mt-1 text-xs text-zinc-500">
          SHA-256 hashed with RPM limits
        </p>
      </div>

      {/* 4. Live Providers Status */}
      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm transition hover:border-zinc-300 dark:border-zinc-800/80 dark:bg-zinc-900/50 dark:hover:border-zinc-700/70">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Provider Mode
          </span>
          <div className="rounded-md bg-zinc-100 p-1.5 text-zinc-700 border border-zinc-200 dark:bg-zinc-800/60 dark:text-zinc-300 dark:border-zinc-700/40">
            <Radio className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex flex-col space-y-1">
          <div className="flex items-center space-x-1.5 text-xs font-mono">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                overview?.live_commandcode_configured
                  ? "bg-emerald-500"
                  : "bg-zinc-400 dark:bg-zinc-600"
              }`}
            />
            <span
              className={
                overview?.live_commandcode_configured
                  ? "text-emerald-600 dark:text-emerald-400 font-medium"
                  : "text-zinc-500 dark:text-zinc-400"
              }
            >
              CommandCode: {overview?.live_commandcode_configured ? "Live (Active)" : "Not Configured"}
            </span>
          </div>
          <div className="flex items-center space-x-1.5 text-xs font-mono">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                overview?.live_gemini_configured
                  ? "bg-emerald-500"
                  : "bg-zinc-400 dark:bg-zinc-600"
              }`}
            />
            <span
              className={
                overview?.live_gemini_configured
                  ? "text-emerald-600 dark:text-emerald-400 font-medium"
                  : "text-zinc-500 dark:text-zinc-400"
              }
            >
              Gemini: {overview?.live_gemini_configured ? "Ready" : "Not Configured"}
            </span>
          </div>
          <div className="flex items-center space-x-1.5 text-xs font-mono">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                overview?.live_openrouter_configured
                  ? "bg-emerald-500"
                  : "bg-zinc-400 dark:bg-zinc-600"
              }`}
            />
            <span
              className={
                overview?.live_openrouter_configured
                  ? "text-emerald-600 dark:text-emerald-400 font-medium"
                  : "text-zinc-500 dark:text-zinc-400"
              }
            >
              OpenRouter: {overview?.live_openrouter_configured ? "Ready" : "Not Configured"}
            </span>
          </div>
        </div>
        <p className="mt-1 text-xs text-zinc-500">
          {overview?.live_commandcode_configured || overview?.live_gemini_configured || overview?.live_openrouter_configured
            ? "Live upstream providers active"
            : "No upstream credentials configured"}
        </p>
      </div>
    </div>
  );
}
