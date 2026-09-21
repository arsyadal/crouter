"use client";

import React, { useEffect, useState } from "react";
import { getHealthReady } from "@/lib/api";
import { Activity, ShieldCheck, Cpu, Terminal } from "lucide-react";

interface NavbarProps {
  activeTab: "routes" | "keys" | "playground";
  setActiveTab: (tab: "routes" | "keys" | "playground") => void;
}

export function Navbar({ activeTab, setActiveTab }: NavbarProps) {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const checkHealth = async () => {
      const ok = await getHealthReady();
      if (mounted) setIsHealthy(ok);
    };
    checkHealth();
    const timer = setInterval(checkHealth, 10000);
    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-[#090d16]/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand & Logo */}
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-500 shadow-md shadow-indigo-500/20">
            <Cpu className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold tracking-tight text-white">
                CRouter
              </span>
              <span className="rounded bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-400 border border-indigo-500/20">
                Gateway v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400">One Gateway. Every Model.</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 rounded-lg bg-slate-900/80 p-1 border border-slate-800">
          <button
            onClick={() => setActiveTab("routes")}
            className={`flex items-center space-x-2 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "routes"
                ? "bg-indigo-600 text-white shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Activity className="h-4 w-4" />
            <span>Routes & Breakers</span>
          </button>
          <button
            onClick={() => setActiveTab("keys")}
            className={`flex items-center space-x-2 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "keys"
                ? "bg-indigo-600 text-white shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            <span>API Keys</span>
          </button>
          <button
            onClick={() => setActiveTab("playground")}
            className={`flex items-center space-x-2 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "playground"
                ? "bg-indigo-600 text-white shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Terminal className="h-4 w-4" />
            <span>Inference Playground</span>
          </button>
        </nav>

        {/* Health Probe Indicator */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                isHealthy === true
                  ? "bg-emerald-500 shadow-sm shadow-emerald-500 animate-pulse"
                  : isHealthy === false
                  ? "bg-rose-500 shadow-sm shadow-rose-500"
                  : "bg-amber-400"
              }`}
            />
            <span className="text-slate-300">
              {isHealthy === true
                ? "Gateway Ready"
                : isHealthy === false
                ? "Gateway Offline"
                : "Probing..."}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
