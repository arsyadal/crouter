from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Admin - Dashboard UI"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CRouter Gateway: Observability & Control Center</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="alternate icon" href="/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['Geist', 'Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
            mono: ['Geist Mono', 'JetBrains Mono', 'ui-monospace', 'monospace'],
          },
          colors: {
            zinc: {
              50: '#fafafa',
              100: '#f4f4f5',
              200: '#e4e4e7',
              300: '#d4d4d8',
              400: '#a1a1aa',
              500: '#71717a',
              600: '#52525b',
              700: '#3f3f46',
              800: '#27272a',
              850: '#1f1f23',
              900: '#18181b',
              950: '#09090b',
            }
          }
        }
      }
    }
  </script>
  <style>
    body {
      font-family: 'Geist', 'Inter', sans-serif;
    }
    code, pre, .font-mono {
      font-family: 'Geist Mono', 'JetBrains Mono', ui-monospace, monospace;
    }
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #d4d4d8; border-radius: 9999px; }
    .dark ::-webkit-scrollbar-thumb { background: #27272a; }
    ::-webkit-scrollbar-thumb:hover { background: #a1a1aa; }
    .dark ::-webkit-scrollbar-thumb:hover { background: #3f3f46; }
  </style>
</head>
<body class="min-h-screen antialiased bg-zinc-50 text-zinc-900 selection:bg-zinc-200 selection:text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 dark:selection:bg-zinc-800 dark:selection:text-zinc-100 transition-colors duration-150 flex flex-col md:flex-row">

  <!-- AUTH GATE MODAL OVERLAY -->
  <div id="auth-gate-modal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm hidden">
    <div class="relative w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900 transition-all">
      <div class="flex items-center gap-3">
        <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100">
          <i data-lucide="lock" class="h-5 w-5"></i>
        </div>
        <div>
          <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100">CRouter Gateway Console Access</h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400">Admin authentication required to manage routes and credentials.</p>
        </div>
      </div>

      <!-- Shadcn Alert Container for Auth Error -->
      <div id="auth-error-alert" class="mt-4 hidden">
        <div class="relative w-full rounded-xl border border-red-200 bg-red-50/80 p-4 text-xs text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200" role="alert">
          <div class="flex items-start space-x-3">
            <i data-lucide="alert-circle" class="h-4 w-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5"></i>
            <div>
              <h5 class="font-semibold uppercase tracking-wider text-[10px] mb-1">Authentication Failed</h5>
              <p id="auth-error-text" class="opacity-90 leading-relaxed"></p>
            </div>
          </div>
        </div>
      </div>

      <form onsubmit="handleAuthSubmit(event)" class="mt-5 space-y-4">
        <div>
          <label for="auth-token-input" class="block text-xs font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
            Master Key or Admin Token
          </label>
          <div class="relative mt-1.5">
            <input
              id="auth-token-input"
              type="password"
              placeholder="Enter master key (e.g. crouter-admin-2026)"
              class="w-full rounded-xl border border-zinc-300 bg-zinc-50 px-3.5 py-2.5 pr-11 text-xs font-mono text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900/10 dark:border-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-zinc-400"
              required
            />
            <button
              type="button"
              onclick="toggleAuthVisibility()"
              class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1.5 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
              aria-label="Toggle password visibility"
            >
              <i id="auth-eye-icon" data-lucide="eye" class="h-4 w-4"></i>
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between rounded-lg border border-dashed border-zinc-200 bg-zinc-50/50 p-2.5 dark:border-zinc-800 dark:bg-zinc-950/40">
          <div class="flex items-center gap-2">
            <i data-lucide="shield-check" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span class="text-[11px] text-zinc-600 dark:text-zinc-400">Local dev default: <code class="font-mono text-zinc-800 dark:text-zinc-200">crouter-admin-2026</code></span>
          </div>
          <button
            type="button"
            onclick="autofillDevToken()"
            class="rounded-md bg-zinc-200/80 px-2 py-1 text-[10px] font-semibold text-zinc-800 hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 transition"
          >
            Autofill
          </button>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2.5">
          <a
            href="/"
            class="min-h-[44px] inline-flex items-center rounded-xl border border-zinc-300 bg-white px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 transition"
          >
            Back to Landing
          </a>
          <button
            type="submit"
            class="min-h-[44px] inline-flex items-center gap-2 rounded-xl bg-zinc-900 px-5 py-2 text-xs font-semibold text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white shadow-sm transition"
          >
            <span>Enter Console</span>
            <i data-lucide="arrow-right" class="h-4 w-4"></i>
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- MOBILE HEADER BAR -->
  <header class="flex h-16 w-full items-center justify-between border-b border-zinc-200 bg-white px-4 md:hidden dark:border-zinc-800 dark:bg-zinc-950">
    <div class="flex items-center space-x-2.5">
      <div class="flex h-7 w-7 items-center justify-center rounded-md border border-zinc-200 bg-zinc-900 text-white dark:border-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 p-1">
        <svg viewBox="0 0 32 32" fill="none" class="h-5 w-5" xmlns="http://www.w3.org/2000/svg">
          <path d="M22.5 10.5C21 8.2 18.3 6.8 15 6.8C9.9 6.8 6 10.9 6 16C6 21.1 9.9 25.2 15 25.2C18.4 25.2 21.2 23.7 22.7 21.3" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
          <circle cx="15" cy="16" r="2.2" fill="#10b981"/>
        </svg>
      </div>
      <div>
        <span class="font-bold text-sm text-zinc-900 dark:text-zinc-100">CRouter</span>
        <span class="ml-1 text-[10px] font-mono text-zinc-400">console</span>
      </div>
    </div>
    <button
      type="button"
      onclick="toggleMobileSidebar()"
      aria-label="Toggle Navigation Menu"
      class="flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900"
    >
      <i id="mobile-menu-icon" data-lucide="menu" class="h-5 w-5"></i>
    </button>
  </header>

  <!-- SIDEBAR NAVIGATION -->
  <aside
    id="sidebar-container"
    class="fixed inset-y-0 left-0 z-40 flex w-72 flex-col justify-between border-r border-zinc-200 bg-white transition-transform duration-200 ease-in-out -translate-x-full md:static md:translate-x-0 dark:border-zinc-800 dark:bg-zinc-950"
  >
    <div class="flex flex-col">
      <!-- Top Branding -->
      <div class="flex h-16 items-center justify-between border-b border-zinc-100 px-5 dark:border-zinc-850">
        <a href="/" class="flex items-center gap-2.5 transition hover:opacity-80" title="CRouter Gateway">
          <div class="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-200 bg-zinc-900 text-white dark:border-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 p-1">
            <svg viewBox="0 0 32 32" fill="none" class="h-6 w-6" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.5 10.5C21 8.2 18.3 6.8 15 6.8C9.9 6.8 6 10.9 6 16C6 21.1 9.9 25.2 15 25.2C18.4 25.2 21.2 23.7 22.7 21.3" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
              <circle cx="15" cy="16" r="2.2" fill="#10b981"/>
            </svg>
          </div>
          <div>
            <span class="font-bold text-sm tracking-tight text-zinc-900 dark:text-zinc-100">CRouter</span>
            <span class="ml-1.5 rounded-sm bg-zinc-100 px-1.5 py-0.5 text-[10px] font-mono font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">Console</span>
          </div>
        </a>
        <div class="flex items-center gap-1.5">
          <span class="relative flex h-2 w-2">
            <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
          </span>
          <span class="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-medium">LIVE</span>
        </div>
      </div>

      <!-- Quick Back Link -->
      <div class="px-4 pt-4 pb-2">
        <a
          href="/"
          class="flex w-full items-center gap-2 rounded-lg border border-zinc-200/70 bg-zinc-50/70 px-3 py-2 text-xs font-medium text-zinc-600 hover:border-zinc-300 hover:bg-zinc-100 hover:text-zinc-900 dark:border-zinc-800/80 dark:bg-zinc-900/50 dark:text-zinc-400 dark:hover:border-zinc-700 dark:hover:bg-zinc-850 dark:hover:text-zinc-200 transition"
        >
          <i data-lucide="arrow-left" class="h-3.5 w-3.5"></i>
          <span>Back to Landing Page</span>
        </a>
      </div>

      <!-- Navigation Modules -->
      <div class="px-3 py-2">
        <div class="px-3 pb-2 pt-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-600 dark:text-zinc-400">
          Gateway Modules
        </div>
        <nav class="space-y-1">
          <button
            id="tab-btn-routes"
            onclick="switchTab('routes')"
            class="group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left text-xs font-medium transition-all bg-zinc-900 text-white shadow-xs dark:bg-zinc-100 dark:text-zinc-900"
          >
            <div class="flex items-center gap-3">
              <i data-lucide="activity" class="h-4 w-4 shrink-0"></i>
              <span class="font-semibold">Routes & Breakers</span>
            </div>
            <i data-lucide="chevron-right" class="h-3.5 w-3.5 opacity-80"></i>
          </button>

          <button
            id="tab-btn-keys"
            onclick="switchTab('keys')"
            class="group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left text-xs font-medium transition-all text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-900 dark:hover:text-zinc-100"
          >
            <div class="flex items-center gap-3">
              <i data-lucide="key-round" class="h-4 w-4 shrink-0"></i>
              <span class="font-semibold">API Keys</span>
            </div>
            <i data-lucide="chevron-right" class="h-3.5 w-3.5 opacity-0 group-hover:opacity-100"></i>
          </button>

          <button
            id="tab-btn-playground"
            onclick="switchTab('playground')"
            class="group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left text-xs font-medium transition-all text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-900 dark:hover:text-zinc-100"
          >
            <div class="flex items-center gap-3">
              <i data-lucide="terminal" class="h-4 w-4 shrink-0"></i>
              <span class="font-semibold">Inference Playground</span>
            </div>
            <i data-lucide="chevron-right" class="h-3.5 w-3.5 opacity-0 group-hover:opacity-100"></i>
          </button>
        </nav>
      </div>
    </div>

    <!-- Bottom Panel -->
    <div class="border-t border-zinc-100 p-4 space-y-3 dark:border-zinc-850">
      <div class="rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-900/40">
        <div class="flex items-center gap-2">
          <i data-lucide="shield-check" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
          <span class="text-xs font-semibold text-zinc-900 dark:text-zinc-100">Master Admin</span>
        </div>
        <p class="mt-1 text-[11px] text-zinc-500 dark:text-zinc-400">OpenAI protocol active on port 8000</p>
      </div>

      <div class="flex items-center justify-between gap-2 pt-1">
        <button
          type="button"
          onclick="toggleTheme()"
          class="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-850 transition"
          aria-label="Toggle color theme"
        >
          <i id="theme-icon" data-lucide="moon" class="h-4 w-4"></i>
          <span>Theme</span>
        </button>
        <button
          type="button"
          onclick="handleLockConsole()"
          class="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white text-xs font-semibold text-red-600 hover:bg-red-50 hover:border-red-200 dark:border-zinc-800 dark:bg-zinc-900 dark:text-red-400 dark:hover:bg-red-950/30 transition"
          title="Lock Console and Return to Landing"
        >
          <i data-lucide="log-out" class="h-4 w-4"></i>
          <span>Lock</span>
        </button>
      </div>
    </div>
  </aside>

  <!-- MAIN CONTENT WRAPPER -->
  <div class="flex-1 flex flex-col min-w-0 overflow-y-auto">
    <main class="flex-1 px-4 py-8 sm:px-8 max-w-7xl w-full mx-auto space-y-8">
      
      <!-- Shadcn Action Alert Notification Banner -->
      <div id="toast-banner-container" class="hidden">
        <div id="toast-banner" class="relative w-full rounded-xl border p-4 text-xs transition-colors" role="alert">
          <div class="flex items-start space-x-3">
            <i id="toast-icon" data-lucide="check-circle-2" class="h-4 w-4 shrink-0 mt-0.5"></i>
            <div>
              <h5 id="toast-title" class="font-semibold uppercase tracking-wider text-[10px] mb-1">Notice</h5>
              <p id="toast-message" class="opacity-90 leading-relaxed"></p>
            </div>
          </div>
        </div>
      </div>

      <!-- Overview Metric Cards -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/50 dark:hover:border-zinc-700">
          <div class="flex items-center justify-between text-zinc-500 dark:text-zinc-400">
            <span class="text-xs font-medium uppercase tracking-wider">Active Routes</span>
            <i data-lucide="activity" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
          </div>
          <div class="mt-2 flex items-baseline space-x-2">
            <span id="metric-routes" class="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">--</span>
            <span class="text-xs text-zinc-500">model aliases</span>
          </div>
          <p class="mt-1 text-[11px] text-zinc-400">Failover priority mapped</p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/50 dark:hover:border-zinc-700">
          <div class="flex items-center justify-between text-zinc-500 dark:text-zinc-400">
            <span class="text-xs font-medium uppercase tracking-wider">Healthy Upstreams</span>
            <i data-lucide="server" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
          </div>
          <div class="mt-2 flex items-baseline space-x-2">
            <span id="metric-upstreams" class="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">--</span>
            <span class="text-xs text-emerald-600 dark:text-emerald-400">100% reachable</span>
          </div>
          <p class="mt-1 text-[11px] text-zinc-400">CommandCode, Gemini, Mock</p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/50 dark:hover:border-zinc-700">
          <div class="flex items-center justify-between text-zinc-500 dark:text-zinc-400">
            <span class="text-xs font-medium uppercase tracking-wider">API Keys Issued</span>
            <i data-lucide="key-round" class="h-4 w-4 text-zinc-700 dark:text-zinc-300"></i>
          </div>
          <div class="mt-2 flex items-baseline space-x-2">
            <span id="metric-keys" class="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">--</span>
            <span class="text-xs text-zinc-500">active tenants</span>
          </div>
          <p class="mt-1 text-[11px] text-zinc-400">Sliding-window RPM enforced</p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/50 dark:hover:border-zinc-700">
          <div class="flex items-center justify-between text-zinc-500 dark:text-zinc-400">
            <span class="text-xs font-medium uppercase tracking-wider">Breakers Tripped</span>
            <i data-lucide="zap-off" class="h-4 w-4 text-amber-500"></i>
          </div>
          <div class="mt-2 flex items-baseline space-x-2">
            <span id="metric-tripped" class="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">0</span>
            <span class="text-xs text-zinc-500">OPEN circuits</span>
          </div>
          <p class="mt-1 text-[11px] text-zinc-400">Self-healing recovery active</p>
        </div>
      </div>

      <!-- MODULE 1: ROUTES & BREAKERS -->
      <section id="tab-routes" class="space-y-6">
        <div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h2 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Routing Policies & Circuit Breakers
            </h2>
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              Live inspection of model routing priorities, circuit breaker failure states, and failover topologies.
            </p>
          </div>
          <button onclick="refreshRoutes()" class="inline-flex items-center space-x-1.5 rounded-lg border border-zinc-200 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 shadow-xs dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 transition">
            <i data-lucide="refresh-cw" class="h-3.5 w-3.5"></i>
            <span>Refresh</span>
          </button>
        </div>

        <div id="routes-container" class="space-y-4">
          <div class="p-8 text-center text-xs text-zinc-400">Loading routing policies...</div>
        </div>
      </section>

      <!-- MODULE 2: API KEYS -->
      <section id="tab-keys" class="hidden space-y-6">
        <div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h2 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Gateway API Key Governance
            </h2>
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              Issue bearer tokens, configure tenant sliding-window rate limits, and enforce inflight concurrency.
            </p>
          </div>
          <div class="flex items-center space-x-2">
            <button onclick="fetchKeys()" class="inline-flex items-center space-x-1.5 rounded-lg border border-zinc-200 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 shadow-xs dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 transition">
              <i data-lucide="refresh-cw" class="h-3.5 w-3.5"></i>
              <span>Refresh</span>
            </button>
            <button onclick="openKeyModal()" class="inline-flex items-center space-x-1.5 rounded-lg bg-zinc-900 px-3.5 py-1.5 text-xs font-medium text-white shadow-xs hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition">
              <i data-lucide="plus" class="h-3.5 w-3.5"></i>
              <span>Create API Key</span>
            </button>
          </div>
        </div>

        <!-- Keys Table Container -->
        <div class="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/40">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-zinc-700 dark:text-zinc-300">
              <thead class="border-b border-zinc-200 bg-zinc-50 uppercase tracking-wider text-zinc-500 font-medium text-[11px] dark:border-zinc-800 dark:bg-zinc-950/70 dark:text-zinc-400">
                <tr>
                  <th class="px-5 py-3 font-medium">Tenant</th>
                  <th class="px-5 py-3 font-medium">Key Prefix</th>
                  <th class="px-5 py-3 font-medium">Rate Limit</th>
                  <th class="px-5 py-3 font-medium">Concurrency</th>
                  <th class="px-5 py-3 font-medium">Status</th>
                  <th class="px-5 py-3 font-medium">Created</th>
                  <th class="px-5 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody id="keys-table-body" class="divide-y divide-zinc-200/80 dark:divide-zinc-800/60">
                <tr><td colspan="7" class="px-5 py-8 text-center text-zinc-400">Loading keys...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- MODULE 3: INFERENCE PLAYGROUND -->
      <section id="tab-playground" class="hidden space-y-6">
        <div>
          <h2 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
            Interactive Inference Playground
          </h2>
          <p class="text-xs text-zinc-500 dark:text-zinc-400">
            Dispatch test requests directly to CRouter gateway, test streaming SSE, and inspect diagnostic headers in real time.
          </p>
        </div>

        <div class="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <!-- Configuration Column -->
          <div class="space-y-4 lg:col-span-5">
            <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm space-y-4 text-xs dark:border-zinc-800 dark:bg-zinc-900/50">
              <div class="flex items-center space-x-2 border-b border-zinc-200 pb-3 dark:border-zinc-800">
                <i data-lucide="sliders" class="h-4 w-4 text-zinc-500"></i>
                <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">Gateway Parameters</h3>
              </div>

              <div class="space-y-4">
                <div>
                  <label class="block font-medium text-zinc-700 dark:text-zinc-300">Gateway API Key (Bearer)</label>
                  <input id="play-key" type="password" placeholder="cr_live_..." class="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs font-mono text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100" />
                </div>

                <div>
                  <label class="block font-medium text-zinc-700 dark:text-zinc-300">Target Model / Alias</label>
                  <select id="play-model" class="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 focus:border-zinc-900 focus:outline-none dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100">
                    <option value="auto/coding">auto/coding (CommandCode Real Upstream: DeepSeek / Ling)</option>
                    <option value="fast/chat">fast/chat (CommandCode -> Gemini -> Mock)</option>
                    <option value="commandcode/deepseek/deepseek-v4-flash">commandcode/deepseek/deepseek-v4-flash</option>
                    <option value="commandcode/inclusionai/ling-3.0-flash-sante:free">commandcode/inclusionai/ling-3.0-flash-sante:free</option>
                    <option value="mock-default">mock-default (Deterministic Mock A -> Mock B)</option>
                  </select>
                </div>

                <div class="flex items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950/60">
                  <span class="font-medium text-zinc-800 dark:text-zinc-200">SSE Streaming Mode</span>
                  <input id="play-stream" type="checkbox" checked class="h-4 w-4 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900 dark:border-zinc-700" />
                </div>
              </div>
            </div>
          </div>

          <!-- Prompt & Output Column -->
          <div class="space-y-4 lg:col-span-7">
            <form onsubmit="sendPlaygroundRequest(event)" class="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <label class="block text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">User Message</label>
              <textarea id="play-prompt" rows="3" required class="mt-2 w-full rounded-md border border-zinc-300 bg-white p-3 text-xs text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100" placeholder="Ask a question or provide instructions...">Explain why a circuit breaker pattern is essential for multi-provider AI inference.</textarea>
              <div class="mt-3 flex items-center justify-between">
                <span class="text-[11px] text-zinc-500 font-mono">POST /v1/chat/completions</span>
                <button id="play-btn" type="submit" class="inline-flex items-center space-x-1.5 rounded-md bg-zinc-900 px-4 py-2 text-xs font-medium text-white shadow-sm hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition">
                  <i data-lucide="send" class="h-3.5 w-3.5"></i>
                  <span>Send Request</span>
                </button>
              </div>
            </form>

            <!-- Diagnostic Headers Box -->
            <div id="diag-headers-box" class="hidden rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-xs dark:border-zinc-800 dark:bg-zinc-950/60">
              <span class="font-semibold uppercase tracking-wider text-zinc-600 dark:text-zinc-400 text-[10px]">Gateway Diagnostic Headers</span>
              <div class="mt-2 grid grid-cols-2 gap-2 font-mono text-[11px] sm:grid-cols-3">
                <div class="p-2 rounded border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900/50">
                  <span class="text-zinc-400 block text-[10px]">Provider:</span>
                  <span id="diag-provider" class="text-zinc-900 dark:text-zinc-100 font-semibold">-</span>
                </div>
                <div class="p-2 rounded border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900/50">
                  <span class="text-zinc-400 block text-[10px]">Upstream Model:</span>
                  <span id="diag-model" class="text-zinc-900 dark:text-zinc-100 font-semibold">-</span>
                </div>
                <div class="p-2 rounded border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900/50">
                  <span class="text-zinc-400 block text-[10px]">Attempts:</span>
                  <span id="diag-attempts" class="text-zinc-900 dark:text-zinc-100 font-semibold">-</span>
                </div>
                <div class="p-2 rounded border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900/50">
                  <span class="text-zinc-400 block text-[10px]">Gateway Latency:</span>
                  <span id="diag-gw-latency" class="text-zinc-900 dark:text-zinc-100 font-semibold">-</span>
                </div>
                <div class="p-2 rounded border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900/50">
                  <span class="text-zinc-400 block text-[10px]">Upstream Latency:</span>
                  <span id="diag-up-latency" class="text-zinc-900 dark:text-zinc-100 font-semibold">-</span>
                </div>
                <div class="p-2 rounded border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900/50">
                  <span class="text-zinc-400 block text-[10px]">Request ID:</span>
                  <span id="diag-req-id" class="text-zinc-900 dark:text-zinc-100 font-semibold text-[10px] truncate">-</span>
                </div>
              </div>
            </div>

            <!-- Output Box -->
            <div class="rounded-xl border border-zinc-200 bg-white shadow-sm overflow-hidden dark:border-zinc-800 dark:bg-zinc-900/50">
              <div class="flex items-center justify-between border-b border-zinc-200 bg-zinc-50/70 px-4 py-2.5 text-xs text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950/60 dark:text-zinc-400">
                <span class="font-medium text-zinc-800 dark:text-zinc-200">Completion Output</span>
                <span id="play-time" class="font-mono text-[11px] text-zinc-400"></span>
              </div>
              <div id="play-output" class="min-h-[160px] p-4 text-xs font-mono text-zinc-800 dark:text-zinc-200 whitespace-pre-wrap leading-relaxed">
                <span class="text-zinc-400 italic">Press "Send Request" to test completion output.</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="mt-auto border-t border-zinc-200/80 dark:border-zinc-800/80 py-6 text-center text-xs text-zinc-500">
      <p>CRouter: Multi-Provider AI Inference Gateway • Built for High Resilience, Zero-Budget Local Mocking & Distributed Telemetry</p>
    </footer>
  </div>

  <!-- KEY CREATION MODAL -->
  <div id="key-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm hidden">
    <div class="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
      <div class="flex items-center justify-between pb-3 border-b border-zinc-200 dark:border-zinc-800">
        <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Create New Gateway API Key</h3>
        <button onclick="closeKeyModal()" class="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"><i data-lucide="x" class="h-4 w-4"></i></button>
      </div>
      <form onsubmit="submitCreateKey(event)" class="mt-4 space-y-4">
        <div>
          <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300">Tenant Name *</label>
          <input id="modal-tenant" type="text" required placeholder="e.g. dev-team, coding-agent" class="mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 text-xs text-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 focus:outline-none" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300">Rate Limit (RPM)</label>
            <input id="modal-rpm" type="number" value="60" min="1" max="10000" class="mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 text-xs text-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 focus:outline-none" />
          </div>
          <div>
            <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300">Max Inflight</label>
            <input id="modal-concurrency" type="number" value="10" min="1" max="500" class="mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 text-xs text-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 focus:outline-none" />
          </div>
        </div>
        <div class="mt-6 flex justify-end space-x-2 pt-4 border-t border-zinc-200 dark:border-zinc-800">
          <button type="button" onclick="closeKeyModal()" class="rounded-md border border-zinc-200 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 transition">Cancel</button>
          <button type="submit" class="rounded-md bg-zinc-900 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition">Generate Key</button>
        </div>
      </form>
    </div>
  </div>

  <!-- KEY CREATED SUCCESS MODAL (WITH SHADCN ALERT) -->
  <div id="key-success-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm hidden">
    <div class="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
      <div class="flex items-center space-x-3 pb-3 border-b border-zinc-200 dark:border-zinc-800">
        <div class="rounded-full bg-emerald-50 p-2 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
          <i data-lucide="check-circle-2" class="h-5 w-5"></i>
        </div>
        <div>
          <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100">API Key Created Successfully</h3>
          <p id="success-tenant-text" class="text-xs text-zinc-500 dark:text-zinc-400"></p>
        </div>
      </div>

      <!-- Shadcn Alert Warning -->
      <div class="mt-4">
        <div class="relative w-full rounded-xl border border-amber-200 bg-amber-50/80 p-4 text-xs text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-200" role="alert">
          <div class="flex items-start space-x-3">
            <i data-lucide="alert-triangle" class="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5"></i>
            <div>
              <h5 class="font-semibold uppercase tracking-wider text-[10px] mb-1">Save this key now</h5>
              <p class="opacity-90 leading-relaxed">For security, only the SHA-256 hash is saved in CRouter database. You will not be able to view this raw token again.</p>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-4">
        <label class="block text-xs font-medium text-zinc-700 dark:text-zinc-300">Generated Bearer Token</label>
        <div class="mt-1 flex items-center space-x-2">
          <input id="success-key-input" type="text" readonly class="w-full rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs font-mono text-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-200 focus:outline-none" />
          <button onclick="copyGeneratedKey()" class="inline-flex items-center space-x-1 rounded-md bg-zinc-900 px-3 py-2 text-xs font-medium text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 shrink-0">
            <i id="copy-success-icon" data-lucide="copy" class="h-3.5 w-3.5"></i>
            <span>Copy</span>
          </button>
        </div>
      </div>

      <div class="mt-6 flex justify-end space-x-2 pt-4 border-t border-zinc-200 dark:border-zinc-800">
        <button onclick="useInPlayground()" class="rounded-md border border-zinc-300 bg-zinc-100 px-3.5 py-1.5 text-xs font-medium text-zinc-800 hover:bg-zinc-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 transition">Use in Playground</button>
        <button onclick="closeSuccessModal()" class="rounded-md border border-zinc-200 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 transition">Close</button>
      </div>
    </div>
  </div>

  <script>
    let rawGeneratedKey = '';
    let isMobileOpen = false;

    // Theme Management
    function initTheme() {
      const savedTheme = localStorage.getItem('crouter-theme') || 'light';
      if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
        updateThemeIcon(true);
      } else {
        document.documentElement.classList.remove('dark');
        updateThemeIcon(false);
      }
    }

    function toggleTheme() {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('crouter-theme', isDark ? 'dark' : 'light');
      updateThemeIcon(isDark);
    }

    function updateThemeIcon(isDark) {
      const icon = document.getElementById('theme-icon');
      if (icon) {
        icon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
        refreshIcons();
      }
    }

    function refreshIcons() {
      if (window.lucide) {
        window.lucide.createIcons();
      }
    }

    // Auth Gate Handling
    function checkAuth() {
      try {
        const auth = JSON.parse(localStorage.getItem('crouter_auth') || '{}');
        if (auth && auth.authenticated) {
          document.getElementById('auth-gate-modal').classList.add('hidden');
          return true;
        }
      } catch (e) {}
      document.getElementById('auth-gate-modal').classList.remove('hidden');
      return false;
    }

    function handleAuthSubmit(e) {
      e.preventDefault();
      const token = document.getElementById('auth-token-input').value.trim();
      const errBox = document.getElementById('auth-error-alert');
      const errText = document.getElementById('auth-error-text');

      if (!token) {
        errText.innerText = 'Please provide a master key or authorization token.';
        errBox.classList.remove('hidden');
        return;
      }

      errBox.classList.add('hidden');
      localStorage.setItem('crouter_auth', JSON.stringify({
        authenticated: true,
        tenant: token === 'crouter-admin-2026' ? 'Master Admin' : 'Gateway Operator',
        timestamp: Date.now()
      }));
      document.getElementById('auth-gate-modal').classList.add('hidden');
      initDashboard();
      showToast('Authenticated successfully as Master Admin');
    }

    function autofillDevToken() {
      document.getElementById('auth-token-input').value = 'crouter-admin-2026';
      document.getElementById('auth-error-alert').classList.add('hidden');
    }

    function toggleAuthVisibility() {
      const input = document.getElementById('auth-token-input');
      const icon = document.getElementById('auth-eye-icon');
      if (input.type === 'password') {
        input.type = 'text';
        icon.setAttribute('data-lucide', 'eye-off');
      } else {
        input.type = 'password';
        icon.setAttribute('data-lucide', 'eye');
      }
      refreshIcons();
    }

    function handleLockConsole() {
      localStorage.removeItem('crouter_auth');
      window.location.href = '/';
    }

    // Mobile Sidebar Drawer
    function toggleMobileSidebar() {
      isMobileOpen = !isMobileOpen;
      const sb = document.getElementById('sidebar-container');
      const icon = document.getElementById('mobile-menu-icon');
      if (isMobileOpen) {
        sb.classList.remove('-translate-x-full');
        icon.setAttribute('data-lucide', 'x');
      } else {
        sb.classList.add('-translate-x-full');
        icon.setAttribute('data-lucide', 'menu');
      }
      refreshIcons();
    }

    // Tab Switching
    function switchTab(tabId) {
      ['routes', 'keys', 'playground'].forEach(t => {
        const sec = document.getElementById('tab-' + t);
        const btn = document.getElementById('tab-btn-' + t);
        if (t === tabId) {
          sec.classList.remove('hidden');
          btn.className = 'group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left text-xs font-medium transition-all bg-zinc-900 text-white shadow-xs dark:bg-zinc-100 dark:text-zinc-900';
          const chevron = btn.querySelector('i[data-lucide="chevron-right"]');
          if (chevron) chevron.classList.remove('opacity-0');
        } else {
          sec.classList.add('hidden');
          btn.className = 'group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left text-xs font-medium transition-all text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-900 dark:hover:text-zinc-100';
          const chevron = btn.querySelector('i[data-lucide="chevron-right"]');
          if (chevron) chevron.classList.add('opacity-0');
        }
      });
      if (window.innerWidth < 768 && isMobileOpen) {
        toggleMobileSidebar();
      }
      refreshIcons();
    }

    // Shadcn Alert Toast
    function showToast(msg, isError = false) {
      const container = document.getElementById('toast-banner-container');
      const banner = document.getElementById('toast-banner');
      const icon = document.getElementById('toast-icon');
      const title = document.getElementById('toast-title');
      const message = document.getElementById('toast-message');

      if (isError) {
        banner.className = 'relative w-full rounded-xl border border-red-200 bg-red-50/80 p-4 text-xs text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200';
        icon.setAttribute('data-lucide', 'alert-circle');
        icon.className = 'h-4 w-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5';
        title.innerText = 'Circuit Breaker Error';
      } else {
        banner.className = 'relative w-full rounded-xl border border-emerald-200 bg-emerald-50/80 p-4 text-xs text-emerald-950 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-200';
        icon.setAttribute('data-lucide', 'check-circle-2');
        icon.className = 'h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5';
        title.innerText = 'System Notification';
      }

      message.innerText = msg;
      container.classList.remove('hidden');
      refreshIcons();
      setTimeout(() => container.classList.add('hidden'), 5000);
    }

    // API Calls: Overview
    async function loadOverview() {
      try {
        const res = await fetch('/admin/overview');
        if (!res.ok) return;
        const d = await res.json();
        document.getElementById('metric-routes').innerText = d.total_routes || '0';
        document.getElementById('metric-upstreams').innerText = d.healthy_upstreams || '0';
        document.getElementById('metric-keys').innerText = d.active_keys || '0';
        document.getElementById('metric-tripped').innerText = d.tripped_breakers || '0';
      } catch (e) {
        console.error('Failed loading overview', e);
      }
    }

    // API Calls: Routes
    async function refreshRoutes() {
      const c = document.getElementById('routes-container');
      try {
        const res = await fetch('/admin/routes');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const routes = await res.json();
        if (!routes.length) {
          c.innerHTML = '<div class="p-8 text-center text-xs text-zinc-400">No active model aliases configured.</div>';
          return;
        }

        c.innerHTML = routes.map(r => {
          let bClass = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20';
          let bIcon = 'check-circle-2';
          if (r.breaker_state === 'OPEN') {
            bClass = 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20';
            bIcon = 'alert-octagon';
          } else if (r.breaker_state === 'HALF-OPEN') {
            bClass = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20';
            bIcon = 'help-circle';
          }

          const hopsHtml = r.hops.map(h => `
            <div class="flex items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50/70 p-2.5 text-xs dark:border-zinc-800 dark:bg-zinc-950/40">
              <div class="flex items-center space-x-2">
                <span class="flex h-5 w-5 items-center justify-center rounded bg-zinc-200 font-mono text-[10px] font-semibold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">P${h.priority}</span>
                <span class="font-medium text-zinc-900 dark:text-zinc-100">${h.provider}</span>
                <span class="font-mono text-zinc-500">(${h.upstream_model})</span>
              </div>
              <span class="rounded bg-zinc-200/80 px-2 py-0.5 font-mono text-[10px] text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">${h.timeout_seconds}s timeout</span>
            </div>
          `).join('');

          return `
            <div class="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/40">
              <div class="flex flex-col justify-between border-b border-zinc-200 bg-zinc-50 px-5 py-3.5 sm:flex-row sm:items-center dark:border-zinc-800 dark:bg-zinc-900/60">
                <div class="flex items-center space-x-3">
                  <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 text-zinc-700 border border-zinc-200 dark:bg-zinc-800/60 dark:text-zinc-300 dark:border-zinc-700/40">
                    <i data-lucide="git-fork" class="h-4 w-4"></i>
                  </div>
                  <div>
                    <div class="flex items-center space-x-2">
                      <span class="font-mono text-sm font-semibold text-zinc-900 dark:text-zinc-100">${r.route_key}</span>
                      <span class="rounded bg-zinc-200/80 px-1.5 py-0.5 font-mono text-[10px] text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">${r.routing_strategy}</span>
                    </div>
                    <p class="text-[11px] text-zinc-500">${r.description || 'Pre-stream failover route'}</p>
                  </div>
                </div>

                <div class="mt-3 flex items-center space-x-2 sm:mt-0">
                  <span class="inline-flex items-center space-x-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${bClass}">
                    <i data-lucide="${bIcon}" class="h-3 w-3"></i>
                    <span>${r.breaker_state}</span>
                  </span>
                  <div class="flex items-center space-x-1 pl-2">
                    <button onclick="resetBreaker('${r.route_key}')" class="rounded-md border border-zinc-200 bg-white px-2 py-1 text-[11px] font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 shadow-xs transition" title="Force Reset to CLOSED">
                      Reset
                    </button>
                    <button onclick="tripBreaker('${r.route_key}')" class="rounded-md border border-zinc-200 bg-white px-2 py-1 text-[11px] font-medium text-amber-700 hover:bg-amber-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-amber-400 shadow-xs transition" title="Force Trip to OPEN">
                      Trip
                    </button>
                  </div>
                </div>
              </div>

              <div class="p-4 space-y-2">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">Upstream Failover Chain</div>
                <div class="space-y-1.5">${hopsHtml}</div>
              </div>
            </div>
          `;
        }).join('');
        refreshIcons();
      } catch (e) {
        c.innerHTML = `<div class="p-8 text-center text-xs text-rose-500">Error loading routes: ${e.message}</div>`;
      }
    }

    async function resetBreaker(routeKey) {
      try {
        const res = await fetch(`/admin/breakers/${encodeURIComponent(routeKey)}/reset`, { method: 'POST' });
        const d = await res.json();
        showToast(d.message || 'Circuit breaker reset to CLOSED');
        refreshRoutes();
        loadOverview();
      } catch (e) {
        showToast(e.message, true);
      }
    }

    async function tripBreaker(routeKey) {
      try {
        const res = await fetch(`/admin/breakers/${encodeURIComponent(routeKey)}/trip`, { method: 'POST' });
        const d = await res.json();
        showToast(d.message || 'Circuit breaker forced to OPEN');
        refreshRoutes();
        loadOverview();
      } catch (e) {
        showToast(e.message, true);
      }
    }

    // API Calls: Keys
    async function fetchKeys() {
      const tbody = document.getElementById('keys-table-body');
      try {
        const res = await fetch('/admin/keys');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const keys = await res.json();
        if (!keys.length) {
          tbody.innerHTML = '<tr><td colspan="7" class="px-5 py-8 text-center text-zinc-400">No gateway keys found. Click "Create API Key" to issue one.</td></tr>';
          return;
        }

        tbody.innerHTML = keys.map(k => `
          <tr class="transition hover:bg-zinc-50 dark:hover:bg-zinc-800/30">
            <td class="px-5 py-3 font-medium text-zinc-900 dark:text-zinc-100">${k.tenant}</td>
            <td class="px-5 py-3 font-mono text-zinc-700 dark:text-zinc-300">${k.key_prefix}...</td>
            <td class="px-5 py-3"><span class="rounded-full border border-zinc-200 bg-zinc-100 px-2.5 py-0.5 font-mono text-zinc-700 text-[11px] dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300">${k.rate_limit_rpm} RPM</span></td>
            <td class="px-5 py-3"><span class="rounded-full border border-zinc-200 bg-zinc-100 px-2.5 py-0.5 font-mono text-zinc-700 text-[11px] dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300">${k.max_concurrency} inflight</span></td>
            <td class="px-5 py-3">${k.is_active ? '<span class="inline-flex items-center space-x-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold dark:bg-emerald-500/10 dark:text-emerald-400">ACTIVE</span>' : '<span class="inline-flex items-center space-x-1 rounded-full bg-zinc-100 text-zinc-600 border border-zinc-200 px-2 py-0.5 text-[11px] font-semibold dark:bg-zinc-800 dark:text-zinc-400">REVOKED</span>'}</td>
            <td class="px-5 py-3 font-mono text-[11px] text-zinc-500">${new Date(k.created_at).toLocaleDateString()}</td>
            <td class="px-5 py-3 text-right">
              ${k.is_active ? `<button onclick="revokeKey('${k.id}')" class="rounded px-2 py-1 text-[11px] font-medium text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40 transition">Revoke</button>` : '<span class="text-zinc-400 text-[11px]">-</span>'}
            </td>
          </tr>
        `).join('');
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="px-5 py-8 text-center text-xs text-rose-500">Error loading keys: ${e.message}</td></tr>`;
      }
    }

    function openKeyModal() { document.getElementById('key-modal').classList.remove('hidden'); }
    function closeKeyModal() { document.getElementById('key-modal').classList.add('hidden'); }

    async function submitCreateKey(e) {
      e.preventDefault();
      const tenant = document.getElementById('modal-tenant').value.trim();
      const rate_limit_rpm = parseInt(document.getElementById('modal-rpm').value, 10);
      const max_concurrency = parseInt(document.getElementById('modal-concurrency').value, 10);

      try {
        const res = await fetch('/admin/keys', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tenant, rate_limit_rpm, max_concurrency })
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Failed to generate key');
        }
        const data = await res.json();
        closeKeyModal();
        rawGeneratedKey = data.key;
        document.getElementById('success-tenant-text').innerText = 'Tenant: ' + data.tenant;
        document.getElementById('success-key-input').value = data.key;
        document.getElementById('key-success-modal').classList.remove('hidden');
        fetchKeys();
        loadOverview();
        refreshIcons();
      } catch (err) {
        alert(err.message);
      }
    }

    function closeSuccessModal() { document.getElementById('key-success-modal').classList.add('hidden'); }

    function copyGeneratedKey() {
      navigator.clipboard.writeText(rawGeneratedKey).then(() => {
        showToast('API key copied to clipboard');
      });
    }

    function useInPlayground() {
      document.getElementById('play-key').value = rawGeneratedKey;
      closeSuccessModal();
      switchTab('playground');
    }

    async function revokeKey(keyId) {
      if (!confirm('Are you sure you want to revoke this API key? This action is irreversible.')) return;
      try {
        const res = await fetch('/admin/keys/' + keyId, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to revoke key');
        showToast('API key revoked successfully');
        fetchKeys();
        loadOverview();
      } catch (e) {
        showToast(e.message, true);
      }
    }

    // API Calls: Playground
    async function sendPlaygroundRequest(e) {
      e.preventDefault();
      const key = document.getElementById('play-key').value.trim();
      const model = document.getElementById('play-model').value.trim();
      const prompt = document.getElementById('play-prompt').value.trim();
      const stream = document.getElementById('play-stream').checked;
      const outBox = document.getElementById('play-output');
      const timeBox = document.getElementById('play-time');
      const diagBox = document.getElementById('diag-headers-box');
      const btn = document.getElementById('play-btn');

      if (!key) {
        alert('Please enter a Gateway API Key first, or generate one in the API Keys tab.');
        return;
      }

      btn.disabled = true;
      outBox.innerText = 'Awaiting tokens from CRouter gateway...';
      diagBox.classList.add('hidden');
      timeBox.innerText = '';
      const startTime = performance.now();

      const messages = [
        { role: 'system', content: 'You are an AI assistant running through CRouter.' },
        { role: 'user', content: prompt }
      ];

      try {
        const res = await fetch('/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + key
          },
          body: JSON.stringify({ model, messages, stream, max_tokens: 256 })
        });

        // Diagnostic headers
        document.getElementById('diag-provider').innerText = res.headers.get('X-CRouter-Provider-Selected') || '-';
        document.getElementById('diag-model').innerText = res.headers.get('X-CRouter-Model-Selected') || '-';
        document.getElementById('diag-attempts').innerText = res.headers.get('X-CRouter-Attempts') || '1';
        document.getElementById('diag-gw-latency').innerText = (res.headers.get('X-CRouter-Latency-Gateway-Ms') || '-') + ' ms';
        document.getElementById('diag-up-latency').innerText = (res.headers.get('X-CRouter-Latency-Upstream-Ms') || '-') + ' ms';
        document.getElementById('diag-req-id').innerText = res.headers.get('X-CRouter-Request-ID') || '-';
        diagBox.classList.remove('hidden');

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error?.message || `HTTP ${res.status}`);
        }

        if (!stream) {
          const data = await res.json();
          outBox.innerText = data.choices?.[0]?.message?.content || JSON.stringify(data, null, 2);
        } else {
          outBox.innerText = '';
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              const trimmed = line.trim();
              if (trimmed.startsWith('data: ')) {
                const jsonStr = trimmed.slice(6);
                if (jsonStr === '[DONE]') break;
                try {
                  const chunk = JSON.parse(jsonStr);
                  const content = chunk.choices?.[0]?.delta?.content || '';
                  outBox.innerText += content;
                } catch (e) {}
              }
            }
          }
        }
        timeBox.innerText = Math.round(performance.now() - startTime) + 'ms elapsed';
      } catch (err) {
        outBox.innerText = 'Error: ' + err.message;
      } finally {
        btn.disabled = false;
      }
    }

    function initDashboard() {
      loadOverview();
      refreshRoutes();
      fetchKeys();
      setInterval(() => {
        loadOverview();
      }, 12000);
    }

    window.onload = () => {
      initTheme();
      refreshIcons();
      if (checkAuth()) {
        initDashboard();
      }
    };
  </script>
</body>
</html>
"""

@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/console", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the CRouter Dashboard & Console with Sidebar navigation and Auth Gate."""
    return DASHBOARD_HTML
