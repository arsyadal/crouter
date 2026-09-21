"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "@/components/Navbar";
import { OverviewCards } from "@/components/OverviewCards";
import { RouteMonitoring } from "@/components/RouteMonitoring";
import { KeyManagement } from "@/components/KeyManagement";
import { ChatPlayground } from "@/components/ChatPlayground";
import {
  OverviewData,
  PolicyDetail,
  KeyItem,
  getOverview,
  getRoutes,
  getKeys,
} from "@/lib/api";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<"routes" | "keys" | "playground">("routes");
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [policies, setPolicies] = useState<PolicyDetail[]>([]);
  const [keys, setKeys] = useState<KeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [playgroundKey, setPlaygroundKey] = useState<string>("");

  const refreshAll = useCallback(async () => {
    try {
      const [ov, rt, ky] = await Promise.allSettled([
        getOverview(),
        getRoutes(),
        getKeys(),
      ]);

      if (ov.status === "fulfilled") setOverview(ov.value);
      if (rt.status === "fulfilled") setPolicies(rt.value);
      if (ky.status === "fulfilled") {
        setKeys(ky.value);
        // Pre-fill playground key with first active key if empty
        const active = ky.value.find((k) => k.is_active);
        if (active && !playgroundKey) {
          // If we have an active key, we can notify or hint in playground
        }
      }
    } finally {
      setLoading(false);
    }
  }, [playgroundKey]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 12000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  const handleKeySelectedForPlayground = (key: string) => {
    setPlaygroundKey(key);
    setActiveTab("playground");
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 selection:bg-indigo-500 selection:text-white">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-8">
        {/* Top Summary Banner & Overview Cards */}
        <OverviewCards overview={overview} loading={loading} />

        {/* Tab Content */}
        <div className="pt-2">
          {activeTab === "routes" && (
            <RouteMonitoring
              policies={policies}
              loading={loading}
              onRefresh={refreshAll}
            />
          )}

          {activeTab === "keys" && (
            <KeyManagement
              keys={keys}
              loading={loading}
              onRefresh={refreshAll}
              onKeySelectedForPlayground={handleKeySelectedForPlayground}
            />
          )}

          {activeTab === "playground" && (
            <ChatPlayground keys={keys} defaultKey={playgroundKey} />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <p>
          CRouter — Multi-Provider AI Inference Gateway • Built for High Resilience, Zero-Budget Local Mocking & Distributed Telemetry
        </p>
      </footer>
    </div>
  );
}
