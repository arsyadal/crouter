"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Sidebar } from "@/components/Sidebar";
import { OverviewCards } from "@/components/OverviewCards";
import { RouteMonitoring } from "@/components/RouteMonitoring";
import { KeyManagement } from "@/components/KeyManagement";
import { ChatPlayground } from "@/components/ChatPlayground";
import { LandingPage } from "@/components/LandingPage";
import { AuthModal } from "@/components/AuthModal";
import {
  OverviewData,
  PolicyDetail,
  KeyItem,
  getOverview,
  getRoutes,
  getKeys,
} from "@/lib/api";

export default function DashboardPage() {
  const [view, setView] = useState<"landing" | "console">("landing");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"routes" | "keys" | "playground">("routes");
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [policies, setPolicies] = useState<PolicyDetail[]>([]);
  const [keys, setKeys] = useState<KeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [playgroundKey, setPlaygroundKey] = useState<string>("");

  // Check persisted auth session on client mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("crouter_auth");
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed && parsed.authenticated) {
            setIsAuthenticated(true);
            const hash = window.location.hash;
            const urlParams = new URLSearchParams(window.location.search);
            if (hash === "#console" || urlParams.get("view") === "console") {
              setView("console");
            }
            return;
          }
        }
      } catch {
        localStorage.removeItem("crouter_auth");
      }

      // If URL explicitly requested console but not authenticated, trigger auth modal
      const hash = window.location.hash;
      const urlParams = new URLSearchParams(window.location.search);
      if (hash === "#console" || urlParams.get("view") === "console") {
        setView("landing");
        setIsAuthModalOpen(true);
      }
    }
  }, []);

  const refreshAll = useCallback(async () => {
    try {
      const [ov, rt, ky] = await Promise.allSettled([
        getOverview(),
        getRoutes(),
        getKeys(),
      ]);

      if (ov.status === "fulfilled") setOverview(ov.value);
      if (rt.status === "fulfilled") setPolicies(rt.value);
      if (ky.status === "fulfilled") setKeys(ky.value);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (view === "console") {
      refreshAll();
      const interval = setInterval(refreshAll, 12000);
      return () => clearInterval(interval);
    }
  }, [view, refreshAll]);

  const handleOpenConsole = () => {
    if (isAuthenticated) {
      setView("console");
      if (typeof window !== "undefined") {
        window.location.hash = "console";
      }
    } else {
      setIsAuthModalOpen(true);
    }
  };

  const handleAuthSuccess = (_token: string) => {
    setIsAuthenticated(true);
    setIsAuthModalOpen(false);
    setView("console");
    if (typeof window !== "undefined") {
      window.location.hash = "console";
    }
  };

  const handleSignOut = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("crouter_auth");
      window.location.hash = "";
    }
    setIsAuthenticated(false);
    setView("landing");
  };

  const handleBackToLanding = () => {
    setView("landing");
    if (typeof window !== "undefined") {
      window.location.hash = "";
    }
  };

  const handleKeySelectedForPlayground = (key: string) => {
    setPlaygroundKey(key);
    setActiveTab("playground");
  };

  if (view === "landing") {
    return (
      <>
        <LandingPage onOpenConsole={handleOpenConsole} />
        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          onSuccess={handleAuthSuccess}
        />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 selection:bg-zinc-200 selection:text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 dark:selection:bg-zinc-800 dark:selection:text-zinc-100 flex flex-col md:flex-row transition-colors duration-150">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onSignOut={handleSignOut}
        onBackToLanding={handleBackToLanding}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <main className="flex-1 px-4 py-8 sm:px-8 max-w-7xl w-full mx-auto space-y-8">
          {/* Top Summary Banner & Overview Cards */}
          <OverviewCards overview={overview} loading={loading} />

          {/* Module Content */}
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
        <footer className="mt-auto border-t border-zinc-200/80 dark:border-zinc-800/80 py-6 text-center text-xs text-zinc-500">
          <p>
            CRouter: Multi-Provider AI Inference Gateway • Built for High Resilience, Zero-Budget Local Mocking & Distributed Telemetry
          </p>
        </footer>
      </div>
    </div>
  );
}
