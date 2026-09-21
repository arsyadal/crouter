"use client";

import React, { useState } from "react";
import { CRouterLogo } from "@/components/CRouterLogo";
import {
  Terminal,
  Cpu,
  ShieldCheck,
  Activity,
  Layers,
  Zap,
  GitFork,
  Copy,
  Check,
  ExternalLink,
  ArrowRight,
  CheckCircle2,
  Radio,
  Clock,
  Code,
  Database,
  Network,
  Server,
  RefreshCw,
  Sun,
  Moon,
  Workflow,
  Lock,
  Boxes,
} from "lucide-react";

interface LandingPageProps {
  onOpenConsole: () => void;
}

export function LandingPage({ onOpenConsole }: LandingPageProps) {
  const [copiedCmd, setCopiedCmd] = useState(false);
  const [activeTabCode, setActiveTabCode] = useState<"curl" | "python" | "cursor">("curl");
  const [isDark, setIsDark] = useState<boolean>(false);

  const installCmd = "git clone https://github.com/arsyadal/crouter.git && cd crouter";

  const handleCopyCmd = () => {
    navigator.clipboard.writeText(installCmd);
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 2000);
  };

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
    <div className="min-h-screen bg-zinc-50 text-zinc-900 selection:bg-zinc-200 selection:text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 dark:selection:bg-zinc-800 dark:selection:text-zinc-100 transition-colors duration-150">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 border-b border-zinc-200/80 bg-white/80 dark:border-zinc-800/80 dark:bg-zinc-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          {/* Logo & Brand */}
          <a href="#hero" className="flex items-center space-x-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 rounded-md">
            <CRouterLogo className="h-8 w-8 shadow-sm rounded-md" />
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
                  CRouter
                </span>
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 border border-zinc-200 dark:bg-zinc-900 dark:text-zinc-400 dark:border-zinc-800">
                  Gateway v1.0
                </span>
              </div>
              <p className="text-[11px] text-zinc-500">One Gateway. Every Model.</p>
            </div>
          </a>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center space-x-6 text-xs font-medium text-zinc-600 dark:text-zinc-400" aria-label="Main Navigation">
            <a href="#routing" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors py-1">
              3-Tier Routing
            </a>
            <a href="#services" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors py-1">
              Protocols
            </a>
            <a href="#providers" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors py-1">
              Providers
            </a>
            <a href="#integrations" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors py-1">
              IDE & CLI
            </a>
            <a href="#features" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors py-1">
              Architecture
            </a>
            <a href="#quickstart" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors py-1">
              Quick Start
            </a>
          </nav>

          {/* Right Action Controls */}
          <div className="flex items-center space-x-3">
            <button
              onClick={toggleTheme}
              className="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-100 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900"
              title="Toggle theme"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            <button
              onClick={onOpenConsole}
              className="inline-flex items-center space-x-2 rounded-md bg-zinc-900 px-3.5 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 focus-visible:ring-offset-2"
            >
              <Activity className="h-3.5 w-3.5" />
              <span>Launch Console</span>
            </button>
          </div>
        </div>
      </header>

      {/* HERO SECTION */}
      <section id="hero" className="relative px-4 pt-16 pb-14 sm:px-6 sm:pt-24 sm:pb-20">
        <div className="mx-auto max-w-5xl text-center space-y-6">
          {/* Status Capsule */}
          <div className="inline-flex items-center space-x-2 rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs text-zinc-700 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60 dark:text-zinc-300">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-mono text-[11px] font-medium">OpenAI-Compatible AI Inference Gateway</span>
          </div>

          {/* Headline */}
          <h1 className="text-3xl font-bold tracking-tight sm:text-5xl lg:text-6xl text-zinc-900 dark:text-zinc-100 leading-tight">
            One Gateway. <br className="hidden sm:inline" />
            70+ Real AI Models. Zero Downtime.
          </h1>

          {/* Subtitle */}
          <p className="mx-auto max-w-2xl text-sm sm:text-base text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Route traffic seamlessly across DeepSeek, Google Gemini, OpenRouter, and CommandCode through a single local endpoint.
            Automatic circuit breakers, latency-based ranking, and distributed rate limiting keep your coding workflow uninterrupted.
          </p>

          {/* Primary Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button
              onClick={onOpenConsole}
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 rounded-md bg-zinc-900 px-6 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 focus-visible:ring-offset-2 min-h-[44px]"
            >
              <span>Open Gateway Console</span>
              <ArrowRight className="h-4 w-4" />
            </button>

            <a
              href="https://github.com/arsyadal/crouter"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 rounded-md border border-zinc-200 bg-white px-5 py-2.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 min-h-[44px]"
            >
              <Code className="h-4 w-4" />
              <span>GitHub Repository</span>
              <ExternalLink className="h-3.5 w-3.5 text-zinc-400" />
            </a>
          </div>

          {/* Quick Copy Command Box */}
          <div className="mx-auto max-w-xl pt-4">
            <div className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-2.5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60">
              <div className="flex items-center space-x-3 overflow-x-auto text-left font-mono text-xs text-zinc-800 dark:text-zinc-200">
                <span className="text-zinc-400 select-none">$</span>
                <span className="select-all">{installCmd}</span>
              </div>
              <button
                onClick={handleCopyCmd}
                className="ml-3 inline-flex items-center space-x-1 rounded p-1.5 text-xs text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 min-h-[32px] min-w-[32px]"
                title="Copy command"
                aria-label="Copy installation command"
              >
                {copiedCmd ? (
                  <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          {/* Core Technical Highlights */}
          <div className="grid grid-cols-2 gap-3 pt-8 sm:grid-cols-4 max-w-4xl mx-auto">
            <div className="rounded-lg border border-zinc-200 bg-white p-3.5 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <div className="text-xl sm:text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100">70+</div>
              <div className="text-xs text-zinc-500 mt-0.5">Real AI Models</div>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-3.5 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <div className="text-xl sm:text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100">3-Tier</div>
              <div className="text-xs text-zinc-500 mt-0.5">Circuit Breaker</div>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-3.5 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <div className="text-xl sm:text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100">&lt; 1ms</div>
              <div className="text-xs text-zinc-500 mt-0.5">Routing Overhead</div>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-3.5 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <div className="text-xl sm:text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100">W3C</div>
              <div className="text-xs text-zinc-500 mt-0.5">Distributed Tracing</div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 1: 3-TIER INTELLIGENT ROUTING */}
      <section id="routing" className="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-7xl space-y-10">
          <div className="max-w-2xl">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
              Intelligent 3-Tier Dynamic Routing
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
              Never let rate limits halt your coding flow. CRouter evaluates provider health and historical latency before forwarding requests, switching upstream paths when limits hit.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tier 1 */}
            <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-4">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800">
                  Tier 1: Primary Fast
                </span>
                <Zap className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Ultra-Fast Flash Models
                </h3>
                <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                  DeepSeek v4 Flash, Ling 3.0 Flash Sante, Gemini 1.5 Flash.
                </p>
              </div>
              <ul className="space-y-2 text-xs text-zinc-600 dark:text-zinc-400">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0" />
                  <span>Sub-second time to first token (TTFT)</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0" />
                  <span>High rate limits for interactive IDE chat</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0" />
                  <span>Tracked with Exponential Moving Average (EMA)</span>
                </li>
              </ul>
            </div>

            {/* Tier 2 */}
            <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-4">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 border border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800">
                  Tier 2: Reasoning & Flagship
                </span>
                <Cpu className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  High-Capability Failover
                </h3>
                <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                  DeepSeek v4 Pro, DeepSeek v4.1 Flash, OpenRouter Llama 3.2.
                </p>
              </div>
              <ul className="space-y-2 text-xs text-zinc-600 dark:text-zinc-400">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-blue-600 flex-shrink-0" />
                  <span>Deep algorithmic reasoning & refactoring</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-blue-600 flex-shrink-0" />
                  <span>Automatic retry with exponential backoff</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-blue-600 flex-shrink-0" />
                  <span>Pre-stream first chunk verification</span>
                </li>
              </ul>
            </div>

            {/* Tier 3 */}
            <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-4">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-semibold text-zinc-700 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700">
                  Tier 3: Offline Sandbox
                </span>
                <ShieldCheck className="h-4 w-4 text-zinc-700 dark:text-zinc-300" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Deterministic Resilience
                </h3>
                <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                  Built-in local mock provider for offline testing and CI/CD runs.
                </p>
              </div>
              <ul className="space-y-2 text-xs text-zinc-600 dark:text-zinc-400">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-zinc-600 flex-shrink-0" />
                  <span>Programmable 429 and 503 fault injection</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-zinc-600 flex-shrink-0" />
                  <span>Zero-budget execution without external keys</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-zinc-600 flex-shrink-0" />
                  <span>Circuit state canary probe validation</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: SERVICE KINDS & PROTOCOLS */}
      <section id="services" className="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6 bg-white dark:bg-zinc-900/30">
        <div className="mx-auto max-w-7xl space-y-10">
          <div className="max-w-2xl">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
              OpenAI-Compatible Protocols & Services
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
              Any client library or IDE expecting standard OpenAI endpoints works out of the box with CRouter. Point your client to localhost:8000/v1.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <div className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2.5">
              <div className="flex items-center space-x-2">
                <div className="rounded-md bg-white p-2 text-zinc-800 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700">
                  <Code className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Chat Completions</h3>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Standard /v1/chat/completions supporting multi-turn dialogues, system instructions, and temperature modulation.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2.5">
              <div className="flex items-center space-x-2">
                <div className="rounded-md bg-white p-2 text-zinc-800 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700">
                  <Radio className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Server-Sent Events (SSE)</h3>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Real-time chunked streaming with text/event-stream headers, pre-stream verification, and graceful mid-stream error trapping.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2.5">
              <div className="flex items-center space-x-2">
                <div className="rounded-md bg-white p-2 text-zinc-800 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700">
                  <Boxes className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Model Aliasing & Discovery</h3>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Endpoint /v1/models exposes both virtual aliases (auto/coding, fast/chat) and concrete upstream model targets.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2.5">
              <div className="flex items-center space-x-2">
                <div className="rounded-md bg-white p-2 text-zinc-800 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700">
                  <Network className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">OpenTelemetry Tracing</h3>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                End-to-end W3C traceparent propagation (00-traceid-spanid-01) with response header X-Trace-ID for distributed debugging.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2.5">
              <div className="flex items-center space-x-2">
                <div className="rounded-md bg-white p-2 text-zinc-800 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700">
                  <Activity className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Prometheus Telemetry</h3>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Standard /metrics scrape target recording request counters, latency percentiles, and circuit breaker trip metrics.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2.5">
              <div className="flex items-center space-x-2">
                <div className="rounded-md bg-white p-2 text-zinc-800 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700">
                  <Lock className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Quota Governance</h3>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                SHA-256 hashed tenant API keys governed by Redis sliding-window limiters and atomic concurrency locks.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3: PROVIDERS & INTEGRATIONS */}
      <section id="providers" className="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-7xl space-y-12">
          {/* Header */}
          <div className="max-w-2xl">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
              Provider Hub & Real Upstream Connectivity
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
              Honest status reporting. CRouter connects to actual upstream APIs and informs you directly when a provider is unconfigured.
            </p>
          </div>

          {/* Providers Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">CommandCode</span>
                <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800">
                  Connected
                </span>
              </div>
              <p className="text-xs text-zinc-500">70+ accessible upstream models (DeepSeek, Ling, Poolside, Claude, GPT).</p>
              <div className="pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
                Active Provider
              </div>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Google Gemini</span>
                <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700">
                  BYOK Optional
                </span>
              </div>
              <p className="text-xs text-zinc-500">Add GEMINI_API_KEY to route requests to Gemini 1.5 Flash and Pro directly.</p>
              <div className="pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
                Native Adapter
              </div>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">OpenRouter</span>
                <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700">
                  BYOK Optional
                </span>
              </div>
              <p className="text-xs text-zinc-500">Add OPENROUTER_API_KEY for open-source model routing (Llama 3.2, Qwen).</p>
              <div className="pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
                Native Adapter
              </div>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Local Sandbox</span>
                <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800">
                  Ready (Port 8001)
                </span>
              </div>
              <p className="text-xs text-zinc-500">Deterministic local mock engine with fault injection for tests.</p>
              <div className="pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
                Built-in Sandbox
              </div>
            </div>
          </div>

          {/* IDE & Tools Row */}
          <div id="integrations" className="pt-6">
            <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
              Tested IDE & CLI Integrations
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {["Cursor IDE", "Claude Code", "OpenAI Codex", "Cline Assistant", "Antigravity", "Python SDK"].map((tool) => (
                <div
                  key={tool}
                  className="rounded-lg border border-zinc-200 bg-white p-3 text-center text-xs font-medium text-zinc-800 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/40 dark:text-zinc-200"
                >
                  <Terminal className="h-4 w-4 mx-auto mb-1.5 text-zinc-500" />
                  {tool}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: CODE EXAMPLES & SETUP */}
      <section id="quickstart" className="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6 bg-white dark:bg-zinc-900/30">
        <div className="mx-auto max-w-7xl space-y-10">
          <div className="max-w-2xl">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
              Connect Any Tool in Seconds
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
              Point your existing scripts, terminal agents, or AI editors to your local CRouter port.
            </p>
          </div>

          {/* Code Tabs */}
          <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
            <div className="flex border-b border-zinc-200 bg-zinc-50/80 px-4 py-2 dark:border-zinc-800 dark:bg-zinc-950/60 text-xs">
              <button
                onClick={() => setActiveTabCode("curl")}
                className={`rounded-md px-3 py-1 font-medium transition ${
                  activeTabCode === "curl"
                    ? "bg-white text-zinc-900 shadow-sm dark:bg-zinc-800 dark:text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200"
                }`}
              >
                cURL
              </button>
              <button
                onClick={() => setActiveTabCode("python")}
                className={`ml-2 rounded-md px-3 py-1 font-medium transition ${
                  activeTabCode === "python"
                    ? "bg-white text-zinc-900 shadow-sm dark:bg-zinc-800 dark:text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200"
                }`}
              >
                Python (OpenAI SDK)
              </button>
              <button
                onClick={() => setActiveTabCode("cursor")}
                className={`ml-2 rounded-md px-3 py-1 font-medium transition ${
                  activeTabCode === "cursor"
                    ? "bg-white text-zinc-900 shadow-sm dark:bg-zinc-800 dark:text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200"
                }`}
              >
                Cursor / Cline Config
              </button>
            </div>

            <div className="p-5 font-mono text-xs text-zinc-800 dark:text-zinc-200 overflow-x-auto leading-relaxed">
              {activeTabCode === "curl" && (
                <pre>{`curl -X POST http://localhost:8000/v1/chat/completions \\
  -H "Authorization: Bearer cr_live_YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "auto/coding",
    "messages": [{"role": "user", "content": "Explain circuit breakers."}],
    "stream": true
  }'`}</pre>
              )}

              {activeTabCode === "python" && (
                <pre>{`from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="cr_live_YOUR_KEY",
)

response = client.chat.completions.create(
    model="auto/coding",
    messages=[{"role": "user", "content": "Write an async worker in Python."}],
    stream=True,
)

for chunk in response:
    content = chunk.choices[0].delta.content or ""
    print(content, end="", flush=True)`}</pre>
              )}

              {activeTabCode === "cursor" && (
                <pre>{`// In Cursor IDE: Settings > Models > OpenAI API Key
// 1. Set API Key: cr_live_YOUR_KEY
// 2. Override Base URL: http://localhost:8000/v1
// 3. Add Model: auto/coding (or deepseek/deepseek-v4-flash)`}</pre>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 5: VERIFIED ARCHITECTURE WORKFLOWS (Honest social proof per R-18) */}
      <section id="features" className="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-7xl space-y-10">
          <div className="max-w-2xl">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
              Verified Production Architecture Workflows
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
              Real infrastructure use cases designed for reliability, distributed tracing, and horizontal pod autoscaling.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                <Workflow className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Zero-Downtime Coding Sessions</span>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                When Tier 1 flash models hit transient 429 rate limits during long refactoring sessions, CRouter switches upstream routes within 50ms without terminating the client socket.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                <Database className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Multi-Tenant Quota Governance</span>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Enforce team limits with sliding-window Redis Lua scripts. Concurrent connection locks prevent runaway test scripts from exhausting your pooled AI budget.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                <Server className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Kubernetes Autoscaling</span>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Cloud-native manifests with Horizontal Pod Autoscaler (HPA) scale gateway instances from 2 to 10 pods based on CPU and memory thresholds under high load.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-zinc-200/80 dark:border-zinc-800/80 py-10 px-4 sm:px-6 text-xs text-zinc-500">
        <div className="mx-auto max-w-7xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2.5">
            <CRouterLogo className="h-5 w-5 rounded" />
            <span className="font-semibold text-zinc-800 dark:text-zinc-200">CRouter</span>
            <span>· One Gateway. Every Model.</span>
          </div>
          <div className="flex items-center space-x-6">
            <a href="#hero" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">
              Back to Top
            </a>
            <button
              onClick={onOpenConsole}
              className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              Control Console
            </button>
            <a
              href="https://github.com/arsyadal/crouter"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              MIT License
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
