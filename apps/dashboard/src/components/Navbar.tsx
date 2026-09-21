"use client";

import React, { useEffect, useState } from "react";
import { getHealthReady } from "@/lib/api";
import { Activity, ShieldCheck, Cpu, Terminal, Sun, Moon } from "lucide-react";
import { CRouterLogo } from "@/components/CRouterLogo";

interface NavbarProps {
  activeTab: "routes" | "keys" | "playground";
  setActiveTab: (tab: "routes" | "keys" | "playground") => void;
  onBackToLanding?: () => void;
}

export function Navbar({ activeTab, setActiveTab, onBackToLanding }: NavbarProps) {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [isDark, setIsDark] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    const checkHealth = async () => {
      const ok = await getHealthReady();
      if (mounted) setIsHealthy(ok);
    };
    checkHealth();
    const timer = setInterval(checkHealth, 10000);

    // Initialize theme from localStorage (default to light)
    const saved = localStorage.getItem("crouter-theme");
    if (saved === "dark") {
      setIsDark(true);
      document.documentElement.classList.add("dark");
    } else {
      setIsDark(false);
      document.documentElement.classList.remove("dark");
    }

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  const toggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    if (nextDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("crouter-theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("crouter-theme", "light");
    }
  };

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200/80 bg-white/80 dark:border-zinc-800/80 dark:bg-zinc-950/80 backdrop-blur-md transition-colors duration-150">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand & Logo */}
        <div className="flex items-center space-x-3">
          <CRouterLogo className="h-8 w-8 shadow-sm rounded-md" />
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
                CRouter
              </span>
              <span className="rounded-full border border-zinc-200 bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
                Gateway v1.0
              </span>
            </div>
            <p className="text-xs text-zinc-500">One Gateway. Every Model.</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 rounded-lg bg-zinc-100 dark:bg-zinc-900/60 p-1 border border-zinc-200/80 dark:border-zinc-800">
          <button
            onClick={() => setActiveTab("routes")}
            className={`flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "routes"
                ? "bg-white text-zinc-950 shadow-sm border border-zinc-200/80 dark:bg-zinc-800 dark:text-zinc-100 dark:border-zinc-700/50"
                : "text-zinc-600 hover:text-zinc-900 hover:bg-zinc-200/50 dark:text-zinc-400 dark:hover:text-zinc-200 dark:hover:bg-zinc-850/50"
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            <span>Routes & Breakers</span>
          </button>
          <button
            onClick={() => setActiveTab("keys")}
            className={`flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "keys"
                ? "bg-white text-zinc-950 shadow-sm border border-zinc-200/80 dark:bg-zinc-800 dark:text-zinc-100 dark:border-zinc-700/50"
                : "text-zinc-600 hover:text-zinc-900 hover:bg-zinc-200/50 dark:text-zinc-400 dark:hover:text-zinc-200 dark:hover:bg-zinc-850/50"
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>API Keys</span>
          </button>
          <button
            onClick={() => setActiveTab("playground")}
            className={`flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "playground"
                ? "bg-white text-zinc-950 shadow-sm border border-zinc-200/80 dark:bg-zinc-800 dark:text-zinc-100 dark:border-zinc-700/50"
                : "text-zinc-600 hover:text-zinc-900 hover:bg-zinc-200/50 dark:text-zinc-400 dark:hover:text-zinc-200 dark:hover:bg-zinc-850/50"
            }`}
          >
            <Terminal className="h-3.5 w-3.5" />
            <span>Inference Playground</span>
          </button>
        </nav>

        {/* Health Probe Indicator & Theme Toggle */}
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-2 rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60">
            <span
              className={`h-2 w-2 rounded-full ${
                isHealthy === true
                  ? "bg-emerald-500 shadow-sm shadow-emerald-500/50 animate-pulse"
                  : isHealthy === false
                  ? "bg-rose-500 shadow-sm shadow-rose-500/50"
                  : "bg-amber-400"
              }`}
            />
            <span className="text-zinc-700 dark:text-zinc-300 font-mono text-[11px]">
              {isHealthy === true
                ? "Gateway Ready"
                : isHealthy === false
                ? "Gateway Offline"
                : "Probing..."}
            </span>
          </div>

          {onBackToLanding && (
            <button
              onClick={onBackToLanding}
              className="inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 bg-white px-2.5 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900"
              title="Return to Landing Page"
            >
              <span>← Landing Page</span>
            </button>
          )}

          <button
            onClick={toggleTheme}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-100 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 transition"
            title="Toggle light/dark mode"
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </header>
  );
}
