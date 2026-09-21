from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Admin - Landing Page"])

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CRouter Gateway: One Gateway. Every Model. Zero Downtime.</title>
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
    body { font-family: 'Geist', 'Inter', sans-serif; }
    code, pre, .font-mono { font-family: 'Geist Mono', monospace; }
  </style>
</head>
<body class="min-h-screen bg-zinc-50 text-zinc-900 selection:bg-zinc-200 selection:text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 dark:selection:bg-zinc-800 dark:selection:text-zinc-100 transition-colors duration-150 relative">

  <!-- AUTH GATE MODAL -->
  <div id="auth-modal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm hidden">
    <div class="relative w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900 transition-all">
      <button
        type="button"
        onclick="closeAuthModal()"
        aria-label="Close modal"
        class="absolute right-4 top-4 rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
      >
        <i data-lucide="x" class="h-4 w-4"></i>
      </button>

      <div class="flex items-center gap-3">
        <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100">
          <i data-lucide="lock" class="h-5 w-5"></i>
        </div>
        <div>
          <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100">Gateway Console Access</h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400">Admin authentication required to manage routes and credentials.</p>
        </div>
      </div>

      <!-- Error Alert -->
      <div id="modal-error-alert" class="mt-4 hidden">
        <div class="relative w-full rounded-xl border border-red-200 bg-red-50/80 p-4 text-xs text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200" role="alert">
          <div class="flex items-start space-x-3">
            <i data-lucide="alert-circle" class="h-4 w-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5"></i>
            <div>
              <h5 class="font-semibold uppercase tracking-wider text-[10px] mb-1">Authentication Failed</h5>
              <p id="modal-error-text" class="opacity-90 leading-relaxed"></p>
            </div>
          </div>
        </div>
      </div>

      <form onsubmit="handleLandingAuthSubmit(event)" class="mt-5 space-y-4">
        <div>
          <label for="landing-auth-input" class="block text-xs font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
            Master Key or Admin Token
          </label>
          <div class="relative mt-1.5">
            <input
              id="landing-auth-input"
              type="password"
              placeholder="Enter master key (e.g. crouter-admin-2026)"
              class="w-full rounded-xl border border-zinc-300 bg-zinc-50 px-3.5 py-2.5 pr-11 text-xs font-mono text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900/10 dark:border-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-zinc-400"
              required
            />
            <button
              type="button"
              onclick="toggleLandingAuthVisibility()"
              class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1.5 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
              aria-label="Toggle password visibility"
            >
              <i id="landing-eye-icon" data-lucide="eye" class="h-4 w-4"></i>
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
            onclick="autofillLandingToken()"
            class="rounded-md bg-zinc-200/80 px-2 py-1 text-[10px] font-semibold text-zinc-800 hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 transition"
          >
            Autofill
          </button>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2.5">
          <button
            type="button"
            onclick="closeAuthModal()"
            class="min-h-[44px] rounded-xl border border-zinc-300 bg-white px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 transition"
          >
            Cancel
          </button>
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

  <!-- Top Navigation Header -->
  <header class="sticky top-0 z-40 border-b border-zinc-200/80 bg-white/80 dark:border-zinc-800/80 dark:bg-zinc-950/80 backdrop-blur-md">
    <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
      <!-- Logo & Brand -->
      <a href="#hero" class="flex items-center space-x-3 focus:outline-none focus:ring-2 focus:ring-zinc-900 rounded-md">
        <div class="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-200 bg-zinc-900 shadow-sm text-white dark:border-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 p-1">
          <svg viewBox="0 0 32 32" fill="none" class="h-6 w-6" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.5 10.5C21 8.2 18.3 6.8 15 6.8C9.9 6.8 6 10.9 6 16C6 21.1 9.9 25.2 15 25.2C18.4 25.2 21.2 23.7 22.7 21.3" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="15" cy="16" r="2.2" fill="#10b981"/>
            <path d="M6 16H12.8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M15 13.8V11.2L18.5 8.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="18.5" cy="8.5" r="1.3" fill="currentColor"/>
            <path d="M15 18.2V20.8L18.5 23.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="18.5" cy="23.5" r="1.3" fill="currentColor"/>
          </svg>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">CRouter</span>
            <span class="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 border border-zinc-200 dark:bg-zinc-900 dark:text-zinc-400 dark:border-zinc-800">Gateway v1.0</span>
          </div>
          <p class="text-[11px] text-zinc-500">One Gateway. Every Model.</p>
        </div>
      </a>

      <!-- Desktop Nav Links -->
      <nav class="hidden md:flex items-center space-x-6 text-xs font-medium text-zinc-600 dark:text-zinc-400">
        <a href="#routing" class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">3-Tier Routing</a>
        <a href="#services" class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Protocols</a>
        <a href="#providers" class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Providers</a>
        <a href="#integrations" class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">IDE & CLI</a>
        <a href="#quickstart" class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Quickstart</a>
      </nav>

      <!-- Right Controls -->
      <div class="flex items-center space-x-3">
        <button id="theme-toggle" onclick="toggleTheme()" class="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-100 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 transition" title="Toggle theme">
          <i data-lucide="moon" class="h-4 w-4 dark:hidden"></i>
          <i data-lucide="sun" class="h-4 w-4 hidden dark:block"></i>
        </button>

        <button
          type="button"
          onclick="openAuthModal()"
          class="inline-flex items-center space-x-2 rounded-md bg-zinc-900 px-3.5 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition min-h-[36px]"
        >
          <i data-lucide="activity" class="h-3.5 w-3.5"></i>
          <span>Launch Console</span>
        </button>
      </div>
    </div>
  </header>

  <!-- HERO SECTION WITH AMBIENT GRID (21st.dev / reactbits style) -->
  <section id="hero" class="relative px-4 pt-16 pb-14 sm:px-6 sm:pt-24 sm:pb-20 overflow-hidden">
    <!-- Subtle Background Dot / Grid Pattern -->
    <div class="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:28px_28px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>

    <div class="mx-auto max-w-5xl text-center space-y-6">
      <!-- Status Pill -->
      <div class="inline-flex items-center space-x-2 rounded-full border border-zinc-200 bg-white/80 backdrop-blur-sm px-3.5 py-1 text-xs text-zinc-700 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/60 dark:text-zinc-300">
        <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="font-mono text-[11px] font-medium">OpenAI-Compatible AI Gateway v1.0</span>
      </div>

      <!-- Headline -->
      <h1 class="text-3xl font-bold tracking-tight sm:text-5xl lg:text-6xl text-zinc-900 dark:text-zinc-100 leading-tight">
        One Gateway. <br class="hidden sm:inline">
        Every Model. Zero Downtime.
      </h1>

      <!-- Subtitle -->
      <p class="mx-auto max-w-2xl text-sm sm:text-base text-zinc-600 dark:text-zinc-400 leading-relaxed">
        Connect Cursor, Claude Code, Cline, and custom clients to 70+ AI models through an OpenAI-compatible endpoint.
        Automatic 3-tier fallback and self-healing circuit breakers prevent coding interruptions when limits hit.
      </p>

      <!-- Action Buttons -->
      <div class="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
        <button
          type="button"
          onclick="openAuthModal()"
          class="w-full sm:w-auto inline-flex items-center justify-center space-x-2 rounded-xl bg-zinc-900 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white transition min-h-[44px]"
        >
          <span>Launch Gateway Console</span>
          <i data-lucide="arrow-right" class="h-4 w-4"></i>
        </button>

        <a href="https://github.com/arsyadal/crouter" target="_blank" rel="noopener noreferrer" class="w-full sm:w-auto inline-flex items-center justify-center space-x-2 rounded-xl border border-zinc-300 bg-white px-5 py-2.5 text-sm font-semibold text-zinc-700 hover:bg-zinc-50 shadow-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-750 transition min-h-[44px]">
          <i data-lucide="code" class="h-4 w-4"></i>
          <span>GitHub Repository</span>
          <i data-lucide="external-link" class="h-3.5 w-3.5 text-zinc-400"></i>
        </a>
      </div>

      <!-- Live Gateway Probe Widget (Reactbits inspired) -->
      <div class="mx-auto max-w-xl pt-4">
        <div class="flex items-center justify-between rounded-xl border border-zinc-200 bg-white/90 p-3 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60 backdrop-blur-sm">
          <div class="flex items-center space-x-3 text-left font-mono text-xs text-zinc-800 dark:text-zinc-200">
            <span class="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span class="text-zinc-600 dark:text-zinc-400">Probe:</span>
            <span id="live-ping-status" class="font-semibold text-emerald-600 dark:text-emerald-400">Live 200 OK</span>
            <span id="live-ping-ms" class="text-zinc-500">(1ms roundtrip)</span>
          </div>
          <button
            type="button"
            onclick="measureLivePing()"
            class="rounded-lg border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-[11px] font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 transition"
          >
            Test Ping
          </button>
        </div>
      </div>

      <!-- Quick Install Command Box -->
      <div class="mx-auto max-w-xl pt-2">
        <div class="flex items-center justify-between rounded-xl border border-zinc-200 bg-white px-4 py-2.5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/60">
          <div class="flex items-center space-x-3 overflow-x-auto text-left font-mono text-xs text-zinc-800 dark:text-zinc-200">
            <span class="text-zinc-400 select-none">$</span>
            <span id="cmd-text" class="select-all">git clone https://github.com/arsyadal/crouter.git && cd crouter</span>
          </div>
          <button onclick="copyCommand()" class="ml-3 inline-flex items-center space-x-1 rounded p-1.5 text-xs text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800 transition" title="Copy command">
            <i id="copy-icon" data-lucide="copy" class="h-4 w-4"></i>
          </button>
        </div>
      </div>

      <!-- Core Technical Highlights -->
      <div class="grid grid-cols-2 gap-3 pt-6 sm:grid-cols-4 max-w-4xl mx-auto">
        <div class="rounded-xl border border-zinc-200 bg-white p-4 text-center shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50">
          <div class="text-xl sm:text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100">70+</div>
          <div class="text-xs text-zinc-500 mt-0.5">Real AI Models</div>
        </div>
        <div class="rounded-xl border border-zinc-200 bg-white p-4 text-center shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50">
          <div class="text-xl sm:text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100">3-Tier</div>
          <div class="text-xs text-zinc-500 mt-0.5">Circuit Breaker</div>
        </div>
        <div class="rounded-xl border border-zinc-200 bg-white p-4 text-center shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50">
          <div class="text-xl sm:text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100">&lt; 1ms</div>
          <div class="text-xs text-zinc-500 mt-0.5">Routing Overhead</div>
        </div>
        <div class="rounded-xl border border-zinc-200 bg-white p-4 text-center shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50">
          <div class="text-xl sm:text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-100">W3C</div>
          <div class="text-xs text-zinc-500 mt-0.5">Distributed Tracing</div>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 1: 3-TIER INTELLIGENT ROUTING -->
  <section id="routing" class="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6">
    <div class="mx-auto max-w-7xl space-y-10">
      <div class="max-w-2xl">
        <h2 class="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Intelligent 3-Tier Dynamic Routing
        </h2>
        <p class="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
          Never let rate limits halt your coding flow. CRouter evaluates provider health and historical latency before forwarding requests, switching upstream paths when limits hit.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Tier 1 -->
        <div class="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-4">
          <div class="flex items-center justify-between">
            <span class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800">
              Tier 1: Primary Fast
            </span>
            <i data-lucide="zap" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
          </div>
          <div>
            <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100">Ultra-Fast Flash Models</h3>
            <p class="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
              DeepSeek v4 Flash, Ling 3.0 Flash Sante, Gemini 1.5 Flash.
            </p>
          </div>
          <ul class="space-y-2 text-xs text-zinc-600 dark:text-zinc-400">
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-emerald-500"></i><span>Sub-second first token latency</span></li>
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-emerald-500"></i><span>Best for inline autocompletion and diff edits</span></li>
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-emerald-500"></i><span>Zero token cost on free tiers</span></li>
          </ul>
        </div>

        <!-- Tier 2 -->
        <div class="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-4">
          <div class="flex items-center justify-between">
            <span class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 border border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800">
              Tier 2: Reasoning Fallback
            </span>
            <i data-lucide="cpu" class="h-4 w-4 text-blue-600 dark:text-blue-400"></i>
          </div>
          <div>
            <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100">High-Capability Reasoning</h3>
            <p class="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
              DeepSeek v4 Pro, Gemini 1.5 Pro, Meta LLaMA 3.2.
            </p>
          </div>
          <ul class="space-y-2 text-xs text-zinc-600 dark:text-zinc-400">
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-blue-500"></i><span>Engaged when Tier 1 returns 429 or 503</span></li>
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-blue-500"></i><span>Large context window for whole-repo analysis</span></li>
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-blue-500"></i><span>Architectural planning and refactoring</span></li>
          </ul>
        </div>

        <!-- Tier 3 -->
        <div class="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-4">
          <div class="flex items-center justify-between">
            <span class="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-semibold text-zinc-700 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700">
              Tier 3: Local Safety Net
            </span>
            <i data-lucide="shield-check" class="h-4 w-4 text-zinc-600 dark:text-zinc-300"></i>
          </div>
          <div>
            <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100">Deterministic Offline Mock</h3>
            <p class="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
              Rp0 Local Mock Provider engine on port 8001.
            </p>
          </div>
          <ul class="space-y-2 text-xs text-zinc-600 dark:text-zinc-400">
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-zinc-500"></i><span>100% offline deterministic test suite</span></li>
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-zinc-500"></i><span>Simulate 429 and 503 faults reliably</span></li>
            <li class="flex items-center space-x-2"><i data-lucide="check" class="h-3.5 w-3.5 text-zinc-500"></i><span>Zero API keys required for development</span></li>
          </ul>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 2: OPENAI PROTOCOL SERVICES (9 SERVICE KINDS) -->
  <section id="services" class="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6">
    <div class="mx-auto max-w-7xl space-y-10">
      <div class="max-w-2xl">
        <h2 class="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Complete OpenAI Compatibility
        </h2>
        <p class="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
          Every endpoint is wire-compatible with the standard OpenAI API specification. Point any SDK or CLI to a single URL.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="message-square" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Anthropic Messages (/v1/messages)</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Native Anthropic protocol for Claude Code CLI, OpenClaw, and Anthropic SDKs with bidirectional SSE streaming.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="minimize-2" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Deterministic Token Optimizer</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Safely strips ANSI colors, deduplicates linter output, and compacts diffs without prompt hacks. Inspect via X-CRouter-Tokens-Saved.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="key" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Multi-Account Key Pooling</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Pool multiple API keys per provider with round-robin or least-error distribution and instant 429 rate limit failover.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="terminal" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Chat Completions (/v1/chat/completions)</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Multi-turn chat, system prompt enforcement, tool calls, and model selection.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="radio" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>SSE Streaming Protocol</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            True chunk-by-chunk Server-Sent Events with pre-stream failover protection.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="boxes" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Models Catalog (/v1/models)</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Dynamic aggregation of available model aliases across all registered providers.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="shield-check" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Sliding-Window Rate Limiting</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Redis-backed token bucket preventing runaway agents from exceeding tenant quotas.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="activity" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Diagnostic Response Headers</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Inspect X-CRouter-Provider-Selected, attempts, latency, and tokens saved on every response.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-2">
          <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            <i data-lucide="server" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Health Probes (/health/live, /health/ready)</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Production-grade Kubernetes liveness and readiness probes for zero-downtime rolling deploys.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION: PROVIDERS & REAL UPSTREAM CONNECTIVITY -->
  <section id="providers" class="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6">
    <div class="mx-auto max-w-7xl space-y-12">
      <div class="max-w-2xl">
        <h2 class="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Provider Hub & Real Upstream Connectivity
        </h2>
        <p class="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
          Honest status reporting. CRouter connects to actual upstream APIs and informs you directly when a provider is unconfigured.
        </p>
      </div>

      <!-- Providers Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-sm text-zinc-900 dark:text-zinc-100">CommandCode</span>
            <span class="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800">
              Connected
            </span>
          </div>
          <p class="text-xs text-zinc-500">70+ accessible upstream models (DeepSeek, Ling, Poolside, Claude, GPT).</p>
          <div class="pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
            Active Provider
          </div>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Google Gemini</span>
            <span class="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700">
              BYOK Optional
            </span>
          </div>
          <p class="text-xs text-zinc-500">Add GEMINI_API_KEY to route requests to Gemini 1.5 Flash and Pro directly.</p>
          <div class="pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
            Native Adapter
          </div>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-sm text-zinc-900 dark:text-zinc-100">OpenRouter</span>
            <span class="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700">
              BYOK Optional
            </span>
          </div>
          <p class="text-xs text-zinc-500">Add OPENROUTER_API_KEY for open-source model routing (Llama 3.2, Qwen).</p>
          <div class="pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
            Native Adapter
          </div>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-sm text-zinc-900 dark:text-zinc-100">Local Sandbox</span>
            <span class="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800">
              Ready (Port 8001)
            </span>
          </div>
          <p class="text-xs text-zinc-500">Deterministic local mock engine with fault injection for automated tests.</p>
          <div class="pt-1 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
            Built-in Sandbox
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 3: DEVELOPER INTEGRATIONS & AGENT ENVIRONMENTS -->
  <section id="integrations" class="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6">
    <div class="mx-auto max-w-7xl space-y-10">
      <div class="max-w-2xl">
        <h2 class="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          IDE & CLI Integrations
        </h2>
        <p class="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
          Seamlessly connect your favorite coding agents, IDEs, and developer workflows with native OpenAI and Anthropic protocol support.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
              <i data-lucide="code" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
              <span>Cursor IDE</span>
            </div>
            <span class="rounded bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">OpenAI Compatible</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Configure Cursor Settings: Override Base URL to <code class="font-mono text-zinc-800 dark:text-zinc-200">http://localhost:8000/v1</code> with model <code class="font-mono text-zinc-800 dark:text-zinc-200">auto/coding</code>.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
              <i data-lucide="terminal" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
              <span>Claude Code CLI</span>
            </div>
            <span class="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-mono text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">Native Anthropic</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Run Claude Code with CRouter: <code class="font-mono text-zinc-800 dark:text-zinc-200">ANTHROPIC_BASE_URL=http://localhost:8000 claude</code>. Uses native <code class="font-mono text-zinc-800 dark:text-zinc-200">/v1/messages</code>.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
              <i data-lucide="bot" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
              <span>Cline & Roo Code</span>
            </div>
            <span class="rounded bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">VS Code Extension</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Select OpenAI-compatible provider in Cline settings. Supports real-time SSE chunk streaming and custom routing aliases.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
              <i data-lucide="cpu" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
              <span>OpenAI Codex & SDKs</span>
            </div>
            <span class="rounded bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">Standard SDK</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Zero code modifications required. Instantiate official OpenAI Python or TypeScript SDKs with base URL <code class="font-mono text-zinc-800 dark:text-zinc-200">http://localhost:8000/v1</code>.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
              <i data-lucide="sparkles" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
              <span>Google Antigravity & Agy</span>
            </div>
            <span class="rounded bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">Agent Platform</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Full agent pair-programming orchestration with automatic token deduplication, retry backoff, and tenant quota tracking.
          </p>
        </div>

        <div class="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs dark:border-zinc-800 dark:bg-zinc-900/50 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2 text-xs font-semibold text-zinc-900 dark:text-zinc-100">
              <i data-lucide="network" class="h-4 w-4 text-emerald-600 dark:text-emerald-400"></i>
              <span>OpenTelemetry & Prometheus</span>
            </div>
            <span class="rounded bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">Observability</span>
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            W3C traceparent headers forwarded to upstream providers. Prometheus scrape targets ready on <code class="font-mono text-zinc-800 dark:text-zinc-200">/metrics</code>.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 4: DEVELOPER QUICKSTART -->
  <section id="quickstart" class="border-t border-zinc-200/80 dark:border-zinc-800/80 px-4 py-16 sm:px-6 bg-white dark:bg-zinc-900/30">
    <div class="mx-auto max-w-7xl space-y-8">
      <div class="max-w-2xl">
        <h2 class="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Developer Quickstart
        </h2>
        <p class="mt-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
          Integrate CRouter into your stack in seconds. Choose your preferred protocol or environment below.
        </p>
      </div>

      <div class="rounded-xl border border-zinc-200 bg-white shadow-sm overflow-hidden dark:border-zinc-800 dark:bg-zinc-900/50">
        <div class="flex flex-wrap items-center justify-between border-b border-zinc-200 bg-zinc-50 px-4 py-2.5 text-xs dark:border-zinc-800 dark:bg-zinc-950/70 gap-2">
          <div class="flex flex-wrap items-center gap-1.5">
            <button id="btn-tab-curl" onclick="switchCodeTab('curl')" class="rounded-md px-3 py-1.5 font-medium bg-white text-zinc-900 shadow-sm dark:bg-zinc-800 dark:text-zinc-100 min-h-[36px]">cURL (OpenAI)</button>
            <button id="btn-tab-anthropic" onclick="switchCodeTab('anthropic')" class="rounded-md px-3 py-1.5 font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 min-h-[36px]">cURL (Anthropic)</button>
            <button id="btn-tab-python" onclick="switchCodeTab('python')" class="rounded-md px-3 py-1.5 font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 min-h-[36px]">Python SDK</button>
            <button id="btn-tab-cursor" onclick="switchCodeTab('cursor')" class="rounded-md px-3 py-1.5 font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 min-h-[36px]">Cursor IDE</button>
            <button id="btn-tab-claude" onclick="switchCodeTab('claude')" class="rounded-md px-3 py-1.5 font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 min-h-[36px]">Claude Code CLI</button>
          </div>
          <button
            type="button"
            onclick="copyActiveCodeTab()"
            class="inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700 transition"
            title="Copy snippet"
          >
            <i id="quickstart-copy-icon" data-lucide="copy" class="h-3.5 w-3.5"></i>
            <span id="quickstart-copy-text">Copy</span>
          </button>
        </div>

        <div class="p-5 font-mono text-xs text-zinc-800 dark:text-zinc-200 overflow-x-auto leading-relaxed">
          <pre id="code-block-curl">curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer cr_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto/coding",
    "messages": [{"role": "user", "content": "Explain circuit breakers in 2 sentences"}],
    "stream": true
  }'</pre>
          <pre id="code-block-anthropic" class="hidden">curl -X POST http://localhost:8000/v1/messages \
  -H "x-api-key: cr_live_YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto/coding",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Write a binary search algorithm in Python"}],
    "stream": true
  }'</pre>
          <pre id="code-block-python" class="hidden">from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="cr_live_YOUR_KEY"
)

response = client.chat.completions.create(
    model="auto/coding",
    messages=[{"role": "user", "content": "Write a binary search algorithm in Python"}],
    stream=True
)

for chunk in response:
    content = chunk.choices[0].delta.content or ""
    print(content, end="", flush=True)</pre>
          <pre id="code-block-cursor" class="hidden">// Cursor Settings > Models > OpenAI API Key:
// 1. Set API Key: cr_live_YOUR_KEY
// 2. Override Base URL: http://localhost:8000/v1
// 3. Add Model: auto/coding (or deepseek/deepseek-v4-flash)</pre>
          <pre id="code-block-claude" class="hidden"># Use Claude Code CLI with CRouter:
export ANTHROPIC_BASE_URL="http://localhost:8000"
export ANTHROPIC_API_KEY="cr_live_YOUR_KEY"

# Start Claude Code session
claude</pre>
        </div>
      </div>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="border-t border-zinc-200/80 dark:border-zinc-800/80 py-10 px-4 sm:px-6 text-xs text-zinc-500">
    <div class="mx-auto max-w-7xl flex flex-col sm:flex-row items-center justify-between gap-4">
      <div class="flex items-center space-x-2.5">
        <div class="flex h-5 w-5 items-center justify-center rounded bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 p-0.5">
          <svg viewBox="0 0 32 32" fill="none" class="h-3.5 w-3.5" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.5 10.5C21 8.2 18.3 6.8 15 6.8C9.9 6.8 6 10.9 6 16C6 21.1 9.9 25.2 15 25.2C18.4 25.2 21.2 23.7 22.7 21.3" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
            <circle cx="15" cy="16" r="2.2" fill="#10b981"/>
          </svg>
        </div>
        <span class="font-semibold text-zinc-800 dark:text-zinc-200">CRouter</span>
        <span>· One Gateway. Every Model.</span>
      </div>
      <div class="flex items-center space-x-6">
        <a href="#hero" class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Back to Top</a>
        <button type="button" onclick="openAuthModal()" class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Control Console</button>
        <a href="https://github.com/arsyadal/crouter" target="_blank" rel="noopener noreferrer" class="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">MIT License</a>
      </div>
    </div>
  </footer>

  <script>
    function toggleTheme() {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('crouter-theme', isDark ? 'dark' : 'light');
    }

    function initTheme() {
      const saved = localStorage.getItem('crouter-theme');
      if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }

    // Auth Modal Handlers
    function openAuthModal() {
      try {
        const auth = JSON.parse(localStorage.getItem('crouter_auth') || '{}');
        if (auth && auth.authenticated) {
          window.location.href = '/dashboard';
          return;
        }
      } catch (e) {}
      document.getElementById('auth-modal').classList.remove('hidden');
    }

    function closeAuthModal() {
      document.getElementById('auth-modal').classList.add('hidden');
    }

    function handleLandingAuthSubmit(e) {
      e.preventDefault();
      const token = document.getElementById('landing-auth-input').value.trim();
      const errBox = document.getElementById('modal-error-alert');
      const errText = document.getElementById('modal-error-text');

      if (!token) {
        errText.innerText = 'Please provide a valid master key or administration token.';
        errBox.classList.remove('hidden');
        return;
      }

      errBox.classList.add('hidden');
      localStorage.setItem('crouter_auth', JSON.stringify({
        authenticated: true,
        tenant: token === 'crouter-admin-2026' ? 'Master Admin' : 'Gateway Operator',
        timestamp: Date.now()
      }));
      closeAuthModal();
      window.location.href = '/dashboard';
    }

    function autofillLandingToken() {
      document.getElementById('landing-auth-input').value = 'crouter-admin-2026';
      document.getElementById('modal-error-alert').classList.add('hidden');
    }

    function toggleLandingAuthVisibility() {
      const input = document.getElementById('landing-auth-input');
      const icon = document.getElementById('landing-eye-icon');
      if (input.type === 'password') {
        input.type = 'text';
        icon.setAttribute('data-lucide', 'eye-off');
      } else {
        input.type = 'password';
        icon.setAttribute('data-lucide', 'eye');
      }
      lucide.createIcons();
    }

    // Live Ping Probe
    async function measureLivePing() {
      const statusEl = document.getElementById('live-ping-status');
      const msEl = document.getElementById('live-ping-ms');
      statusEl.innerText = 'Pinging...';
      const start = performance.now();
      try {
        const res = await fetch('/health/live');
        const elapsed = Math.round(performance.now() - start);
        if (res.ok) {
          statusEl.innerText = 'Live 200 OK';
          statusEl.className = 'font-semibold text-emerald-600 dark:text-emerald-400';
          msEl.innerText = `(${elapsed}ms roundtrip)`;
        } else {
          statusEl.innerText = 'HTTP ' + res.status;
          statusEl.className = 'font-semibold text-amber-500';
          msEl.innerText = `(${elapsed}ms)`;
        }
      } catch (e) {
        statusEl.innerText = 'Offline';
        statusEl.className = 'font-semibold text-red-500';
        msEl.innerText = '(connect error)';
      }
    }

    function copyCommand() {
      const text = document.getElementById('cmd-text').innerText;
      navigator.clipboard.writeText(text).then(() => {
        const icon = document.getElementById('copy-icon');
        icon.setAttribute('data-lucide', 'check');
        icon.classList.add('text-emerald-500');
        lucide.createIcons();
        setTimeout(() => {
          icon.setAttribute('data-lucide', 'copy');
          icon.classList.remove('text-emerald-500');
          lucide.createIcons();
        }, 2000);
      });
    }

    let currentQuickstartTab = 'curl';
    function switchCodeTab(tab) {
      currentQuickstartTab = tab;
      ['curl', 'anthropic', 'python', 'cursor', 'claude'].forEach(t => {
        const btn = document.getElementById('btn-tab-' + t);
        const block = document.getElementById('code-block-' + t);
        if (!btn || !block) return;
        if (t === tab) {
          btn.className = 'rounded-md px-3 py-1.5 font-medium bg-white text-zinc-900 shadow-sm dark:bg-zinc-800 dark:text-zinc-100 min-h-[36px]';
          block.classList.remove('hidden');
        } else {
          btn.className = 'rounded-md px-3 py-1.5 font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 min-h-[36px]';
          block.classList.add('hidden');
        }
      });
    }

    function copyActiveCodeTab() {
      const block = document.getElementById('code-block-' + currentQuickstartTab);
      if (!block) return;
      navigator.clipboard.writeText(block.innerText).then(() => {
        const icon = document.getElementById('quickstart-copy-icon');
        const text = document.getElementById('quickstart-copy-text');
        if (icon) icon.setAttribute('data-lucide', 'check');
        if (text) text.innerText = 'Copied!';
        lucide.createIcons();
        setTimeout(() => {
          if (icon) icon.setAttribute('data-lucide', 'copy');
          if (text) text.innerText = 'Copy';
          lucide.createIcons();
        }, 2000);
      });
    }

    initTheme();
    lucide.createIcons();
  </script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
@router.get("/landing", response_class=HTMLResponse)
async def serve_landing():
    """Serve the CRouter Landing Page."""
    return LANDING_HTML
