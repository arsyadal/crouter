"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  KeyRound,
  Terminal,
  LogOut,
  Sun,
  Moon,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Menu,
  X,
  ChevronRight,
  ArrowLeft,
} from "lucide-react";
import { CRouterLogo } from "./CRouterLogo";

interface SidebarProps {
  activeTab: "routes" | "keys" | "playground";
  setActiveTab: (tab: "routes" | "keys" | "playground") => void;
  onSignOut: () => void;
  onBackToLanding: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  onSignOut,
  onBackToLanding,
}) => {
  const [isDark, setIsDark] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedTheme = localStorage.getItem("crouter-theme");
      if (savedTheme === "dark") {
        document.documentElement.classList.add("dark");
        setIsDark(true);
      } else {
        document.documentElement.classList.remove("dark");
        setIsDark(false);
      }
    }
  }, []);

  const toggleTheme = () => {
    const root = document.documentElement;
    if (root.classList.contains("dark")) {
      root.classList.remove("dark");
      localStorage.setItem("crouter-theme", "light");
      setIsDark(false);
    } else {
      root.classList.add("dark");
      localStorage.setItem("crouter-theme", "dark");
      setIsDark(true);
    }
  };

  const navItems = [
    {
      id: "routes" as const,
      label: "Routes & Breakers",
      description: "Circuit breaker status and upstream hops",
      icon: Activity,
    },
    {
      id: "keys" as const,
      label: "API Keys",
      description: "Tenant credentials, RPM and concurrency",
      icon: KeyRound,
    },
    {
      id: "playground" as const,
      label: "Inference Playground",
      description: "Live test with streaming telemetry",
      icon: Terminal,
    },
  ];

  return (
    <>
      {/* Mobile Header Bar */}
      <header className="flex h-16 w-full items-center justify-between border-b border-zinc-200 bg-white px-4 md:hidden dark:border-zinc-800 dark:bg-zinc-950">
        <button
          type="button"
          onClick={onBackToLanding}
          className="flex items-center gap-2.5 text-left focus-visible:outline-none"
        >
          <CRouterLogo className="h-7 w-7" />
          <div>
            <span className="font-bold text-sm text-zinc-900 dark:text-zinc-100">CRouter</span>
            <span className="ml-1.5 text-[10px] font-mono text-zinc-400">console</span>
          </div>
        </button>
        <button
          type="button"
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          aria-label={isMobileOpen ? "Close menu" : "Open menu"}
          className="flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900 focus-visible:ring-2 focus-visible:ring-zinc-400"
        >
          {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </header>

      {/* Mobile Drawer Backdrop */}
      {isMobileOpen && (
        <div
          role="presentation"
          onClick={() => setIsMobileOpen(false)}
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-xs md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col justify-between border-r border-zinc-200 bg-white transition-transform duration-200 ease-in-out md:static md:translate-x-0 dark:border-zinc-800 dark:bg-zinc-950 ${
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Top Branding */}
        <div className="flex flex-col">
          <div className="flex h-16 items-center justify-between border-b border-zinc-100 px-5 dark:border-zinc-850">
            <button
              type="button"
              onClick={onBackToLanding}
              className="flex items-center gap-2.5 rounded-lg text-left transition hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500"
              title="Return to Landing Page"
            >
              <CRouterLogo className="h-7 w-7" />
              <div>
                <span className="font-bold text-sm tracking-tight text-zinc-900 dark:text-zinc-100">
                  CRouter
                </span>
                <span className="ml-1.5 rounded-sm bg-zinc-100 px-1.5 py-0.5 text-[10px] font-mono font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                  Console
                </span>
              </div>
            </button>
            <div className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
              </span>
              <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-medium">
                LIVE
              </span>
            </div>
          </div>

          {/* Quick Return Link */}
          <div className="px-4 pt-4 pb-2">
            <button
              type="button"
              onClick={onBackToLanding}
              className="flex w-full items-center gap-2 rounded-lg border border-zinc-200/70 bg-zinc-50/70 px-3 py-2 text-xs font-medium text-zinc-600 hover:border-zinc-300 hover:bg-zinc-100 hover:text-zinc-900 dark:border-zinc-800/80 dark:bg-zinc-900/50 dark:text-zinc-400 dark:hover:border-zinc-700 dark:hover:bg-zinc-850 dark:hover:text-zinc-200 transition"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Landing Page</span>
            </button>
          </div>

          {/* Navigation Section */}
          <div className="px-3 py-2">
            <div className="px-3 pb-2 pt-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-600 dark:text-zinc-400">
              Gateway Modules
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setActiveTab(item.id);
                      setIsMobileOpen(false);
                    }}
                    className={`group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left text-xs font-medium transition-all ${
                      isActive
                        ? "bg-zinc-900 text-white shadow-xs dark:bg-zinc-100 dark:text-zinc-900"
                        : "text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-900 dark:hover:text-zinc-100"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Icon
                        className={`h-4 w-4 shrink-0 transition-colors ${
                          isActive
                            ? "text-white dark:text-zinc-900"
                            : "text-zinc-600 group-hover:text-zinc-800 dark:text-zinc-400 dark:group-hover:text-zinc-200"
                        }`}
                      />
                      <div className="truncate">
                        <div className="font-semibold leading-tight">{item.label}</div>
                      </div>
                    </div>
                    <ChevronRight
                      className={`h-3.5 w-3.5 transition-transform ${
                        isActive
                          ? "text-white/80 dark:text-zinc-900/80 translate-x-0.5"
                          : "text-zinc-500 opacity-0 group-hover:opacity-100"
                      }`}
                    />
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Bottom Panel */}
        <div className="border-t border-zinc-100 p-4 space-y-3 dark:border-zinc-850">
          {/* Operator Badge */}
          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-900/40">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                Master Admin
              </span>
            </div>
            <p className="mt-1 text-[11px] text-zinc-500 dark:text-zinc-400">
              OpenAI protocol gateway active on port 8000
            </p>
          </div>

          {/* Controls: Theme & Sign Out */}
          <div className="flex items-center justify-between gap-2 pt-1">
            <button
              type="button"
              onClick={toggleTheme}
              className="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-850 transition"
              aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? <Sun className="h-4 w-4 text-amber-500" /> : <Moon className="h-4 w-4 text-zinc-600" />}
              <span>{isDark ? "Light" : "Dark"}</span>
            </button>
            <button
              type="button"
              onClick={onSignOut}
              className="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white text-xs font-semibold text-red-600 hover:bg-red-50 hover:border-red-200 dark:border-zinc-800 dark:bg-zinc-900 dark:text-red-400 dark:hover:bg-red-950/30 dark:hover:border-red-900/50 transition"
              title="Sign out and return to landing page"
            >
              <LogOut className="h-4 w-4" />
              <span>Lock</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
