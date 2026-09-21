from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Admin - Visual Web Dashboard"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CRouter Gateway — Observability & Control Center</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#eef2ff',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
            }
          }
        }
      }
    }
  </script>
  <style>
    body { background-color: #090d16; color: #f8fafc; font-family: ui-sans-serif, system-ui, sans-serif; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
  </style>
</head>
<body class="min-h-screen antialiased selection:bg-indigo-500 selection:text-white">
  <!-- Top Navigation -->
  <header class="sticky top-0 z-40 border-b border-slate-800 bg-[#090d16]/90 backdrop-blur">
    <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
      <div class="flex items-center space-x-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-500 shadow-md shadow-indigo-500/20 text-white font-black text-xl">
          CR
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="text-lg font-bold tracking-tight text-white">CRouter</span>
            <span class="rounded bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-400 border border-indigo-500/20">Gateway v1.0</span>
          </div>
          <p class="text-xs text-slate-400">One Gateway. Every Model.</p>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <nav class="flex space-x-1 rounded-lg bg-slate-900/80 p-1 border border-slate-800 text-xs">
        <button id="tab-btn-routes" onclick="switchTab('routes')" class="flex items-center space-x-2 rounded-md px-3.5 py-1.5 font-medium transition bg-indigo-600 text-white shadow">
          <span>Routes & Breakers</span>
        </button>
        <button id="tab-btn-keys" onclick="switchTab('keys')" class="flex items-center space-x-2 rounded-md px-3.5 py-1.5 font-medium transition text-slate-400 hover:text-white">
          <span>API Keys</span>
        </button>
        <button id="tab-btn-playground" onclick="switchTab('playground')" class="flex items-center space-x-2 rounded-md px-3.5 py-1.5 font-medium transition text-slate-400 hover:text-white">
          <span>Inference Playground</span>
        </button>
      </nav>

      <!-- Status Indicator -->
      <div class="flex items-center space-x-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs">
        <span id="health-dot" class="h-2 w-2 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500 animate-pulse"></span>
        <span id="health-text" class="text-slate-300">Gateway Ready</span>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-8">
    <!-- Overview Cards -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 shadow-sm backdrop-blur">
        <div class="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-slate-400">
          <span>Active Routes</span>
          <span class="rounded bg-indigo-500/10 px-2 py-0.5 text-indigo-400">Alias</span>
        </div>
        <div class="mt-3 flex items-baseline space-x-2">
          <span id="stat-routes-count" class="text-2xl font-bold text-white">-</span>
          <span id="stat-hops-count" class="text-xs text-slate-400">hops</span>
        </div>
        <p class="mt-1 text-xs text-slate-500">auto/coding, fast/chat, etc.</p>
      </div>

      <div class="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 shadow-sm backdrop-blur">
        <div class="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-slate-400">
          <span>Circuit Breaker Health</span>
          <span class="rounded bg-emerald-500/10 px-2 py-0.5 text-emerald-400">State</span>
        </div>
        <div class="mt-3 flex items-baseline space-x-2">
          <span id="stat-breaker-status" class="text-2xl font-bold text-emerald-400">All Healthy</span>
        </div>
        <p class="mt-1 text-xs text-slate-500">Auto-trips on 5 consecutive 5xx</p>
      </div>

      <div class="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 shadow-sm backdrop-blur">
        <div class="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-slate-400">
          <span>Authenticated Keys</span>
          <span class="rounded bg-cyan-500/10 px-2 py-0.5 text-cyan-400">Tenants</span>
        </div>
        <div class="mt-3 flex items-baseline space-x-2">
          <span id="stat-keys-active" class="text-2xl font-bold text-white">-</span>
          <span id="stat-keys-total" class="text-xs text-slate-400">active</span>
        </div>
        <p class="mt-1 text-xs text-slate-500">SHA-256 hashed with RPM limits</p>
      </div>

      <div class="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 shadow-sm backdrop-blur">
        <div class="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-slate-400">
          <span>Live Provider BYOK</span>
          <span class="rounded bg-amber-500/10 px-2 py-0.5 text-amber-400">Mode</span>
        </div>
        <div class="mt-2 space-y-1 text-xs">
          <div class="flex items-center space-x-1.5">
            <span id="dot-gemini" class="h-1.5 w-1.5 rounded-full bg-slate-600"></span>
            <span id="label-gemini" class="text-slate-400">Gemini: Rp0 Mock</span>
          </div>
          <div class="flex items-center space-x-1.5">
            <span id="dot-openrouter" class="h-1.5 w-1.5 rounded-full bg-slate-600"></span>
            <span id="label-openrouter" class="text-slate-400">OpenRouter: Rp0 Mock</span>
          </div>
        </div>
        <p class="mt-1 text-xs text-slate-500">Modal Rp0 local mock default</p>
      </div>
    </div>

    <!-- Alert / Toast Banner -->
    <div id="toast-banner" class="hidden rounded-lg p-3 text-xs border"></div>

    <!-- TAB 1: Routes & Breakers -->
    <section id="tab-routes" class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-white">Routing Policies & Circuit Breakers</h2>
          <p className="text-xs text-slate-400">Inspect active model aliases, provider fallback chains, and circuit breaker trip mechanics.</p>
        </div>
        <button onclick="loadRoutes()" class="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700">
          ↻ Refresh Routes
        </button>
      </div>
      <div id="policies-container" class="space-y-4"></div>
    </section>

    <!-- TAB 2: API Keys -->
    <section id="tab-keys" class="hidden space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-white">Gateway API Key Governance</h2>
          <p class="text-xs text-slate-400">Manage tenant-scoped API keys with sliding-window rate limits and concurrency ceilings.</p>
        </div>
        <div class="flex items-center space-x-3">
          <button onclick="loadKeys()" class="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700">
            ↻ Refresh
          </button>
          <button onclick="openCreateKeyModal()" class="rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500">
            + Create API Key
          </button>
        </div>
      </div>

      <div class="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
        <table class="w-full text-left text-xs text-slate-300">
          <thead class="border-b border-slate-800 bg-slate-950/40 uppercase tracking-wider text-slate-400">
            <tr>
              <th class="px-5 py-3 font-medium">Tenant</th>
              <th class="px-5 py-3 font-medium">Key Prefix</th>
              <th class="px-5 py-3 font-medium">Rate Limit</th>
              <th class="px-5 py-3 font-medium">Concurrency</th>
              <th class="px-5 py-3 font-medium">Status</th>
              <th class="px-5 py-3 font-medium">Created</th>
              <th class="px-5 py-3 text-right font-medium">Action</th>
            </tr>
          </thead>
          <tbody id="keys-table-body" class="divide-y divide-slate-800/60"></tbody>
        </table>
      </div>
    </section>

    <!-- TAB 3: Playground -->
    <section id="tab-playground" class="hidden space-y-6">
      <div>
        <h2 class="text-lg font-bold text-white">Interactive Inference Playground</h2>
        <p class="text-xs text-slate-400">Test live or mock inference, stream tokens via SSE, and inspect diagnostic headers.</p>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <!-- Controls Column -->
        <div class="space-y-4 lg:col-span-5">
          <div class="rounded-xl border border-slate-800 bg-slate-900/40 p-5 shadow-sm space-y-4 text-xs">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-2">
              Inference Configuration
            </h3>

            <div>
              <label class="block font-medium text-slate-300">Gateway API Key (Bearer)</label>
              <input id="play-key" type="password" placeholder="cr_live_..." class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none">
            </div>

            <div>
              <label class="block font-medium text-slate-300">Model Alias / Target</label>
              <select id="play-model" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none">
                <option value="auto/coding">auto/coding (Mock Priority Failover)</option>
                <option value="fast/chat">fast/chat (Gemini → OpenRouter → Mock)</option>
                <option value="mock-a">mock-a (Deterministic Mock A)</option>
                <option value="mock-b">mock-b (Deterministic Mock B)</option>
                <option value="gemini-1.5-flash">gemini-1.5-flash (Google Gemini Direct)</option>
                <option value="openrouter/meta-llama/llama-3.2-3b-instruct:free">openrouter/llama-3.2-3b-instruct:free</option>
              </select>
            </div>

            <div class="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <div>
                <span class="font-medium text-white">SSE Streaming</span>
                <p class="text-[11px] text-slate-400">Stream tokens chunk-by-chunk</p>
              </div>
              <input id="play-stream" type="checkbox" checked class="h-4 w-4 rounded accent-indigo-600">
            </div>

            <div>
              <label class="block font-medium text-slate-300">System Instruction</label>
              <textarea id="play-system" rows="2" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none">You are a helpful platform engineering AI assistant running through CRouter.</textarea>
            </div>
          </div>
        </div>

        <!-- Chat Area -->
        <div class="space-y-4 lg:col-span-7">
          <div class="rounded-xl border border-slate-800 bg-slate-900/40 p-4 shadow-sm">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-400">User Prompt</label>
            <textarea id="play-prompt" rows="3" class="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none">Explain how CRouter performs zero-downtime failover across AI models.</textarea>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-[11px] text-slate-400 font-mono">POST /v1/chat/completions</span>
              <button id="btn-send" onclick="sendInference()" class="rounded-lg bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 transition">
                Send Request
              </button>
            </div>
          </div>

          <!-- Diagnostic Headers Box -->
          <div id="diag-headers-box" class="hidden rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-4 text-xs">
            <div class="text-[11px] font-bold text-indigo-300 uppercase tracking-wider pb-2 border-b border-indigo-500/20">
              Response Diagnostics (X-CRouter Headers)
            </div>
            <div class="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div class="rounded bg-slate-900/80 p-2 border border-slate-800">
                <span class="text-[10px] text-slate-400 uppercase block">Provider Selected</span>
                <span id="diag-provider" class="font-bold text-white text-xs">-</span>
              </div>
              <div class="rounded bg-slate-900/80 p-2 border border-slate-800">
                <span class="text-[10px] text-slate-400 uppercase block">Upstream Model</span>
                <span id="diag-model" class="font-mono text-slate-200 text-xs">-</span>
              </div>
              <div class="rounded bg-slate-900/80 p-2 border border-slate-800">
                <span class="text-[10px] text-slate-400 uppercase block">Routing Attempts</span>
                <span id="diag-attempts" class="font-bold text-emerald-400 text-xs">-</span>
              </div>
              <div class="rounded bg-slate-900/80 p-2 border border-slate-800">
                <span class="text-[10px] text-slate-400 uppercase block">Gateway Latency</span>
                <span id="diag-gw-latency" class="font-mono text-cyan-300 text-xs">-</span>
              </div>
              <div class="rounded bg-slate-900/80 p-2 border border-slate-800">
                <span class="text-[10px] text-slate-400 uppercase block">Upstream Latency</span>
                <span id="diag-up-latency" class="font-mono text-indigo-300 text-xs">-</span>
              </div>
              <div class="rounded bg-slate-900/80 p-2 border border-slate-800">
                <span class="text-[10px] text-slate-400 uppercase block">Request Trace ID</span>
                <span id="diag-req-id" class="font-mono text-[10px] text-slate-400 truncate block">-</span>
              </div>
            </div>
          </div>

          <!-- Output Box -->
          <div class="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
            <div class="flex items-center justify-between border-b border-slate-800 bg-slate-950/60 px-4 py-2.5 text-xs text-slate-400">
              <span class="font-medium text-slate-300">Completion Output</span>
              <span id="play-status-indicator">Ready</span>
            </div>
            <div id="play-output" class="min-h-[160px] p-4 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">Press "Send Request" to test inference.</div>
          </div>
        </div>
      </div>
    </section>
  </main>

  <!-- Create Key Modal -->
  <div id="modal-create-key" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
    <div class="w-full max-w-md rounded-2xl border border-slate-800 bg-[#0f172a] p-6 shadow-2xl space-y-4">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-base font-bold text-white">Create Gateway API Key</h3>
        <button onclick="closeCreateKeyModal()" class="text-slate-400 hover:text-white">✕</button>
      </div>

      <div class="space-y-3 text-xs">
        <div>
          <label class="block font-medium text-slate-300">Tenant Name *</label>
          <input id="input-tenant" type="text" placeholder="e.g. sdcraft, internal-service" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-medium text-slate-300">Rate Limit (RPM)</label>
            <input id="input-rpm" type="number" value="60" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none">
          </div>
          <div>
            <label class="block font-medium text-slate-300">Max Concurrency</label>
            <input id="input-concurrency" type="number" value="10" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none">
          </div>
        </div>
      </div>

      <div class="flex justify-end space-x-3 pt-3 border-t border-slate-800">
        <button onclick="closeCreateKeyModal()" class="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800">Cancel</button>
        <button onclick="submitCreateKey()" class="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500">Generate Token</button>
      </div>
    </div>
  </div>

  <!-- Key Created Modal (Raw Secret Token) -->
  <div id="modal-key-success" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
    <div class="w-full max-w-lg rounded-2xl border border-indigo-500/40 bg-[#0f172a] p-6 shadow-2xl space-y-4">
      <h3 class="text-base font-bold text-white">API Key Issued Successfully</h3>
      <div class="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 text-xs text-amber-300">
        <strong>Save this key now!</strong> Only the SHA-256 hash is saved in database. This raw token will never be displayed again.
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-300">Generated Bearer Token</label>
        <div class="mt-1 flex items-center space-x-2">
          <input id="success-key-token" type="text" readonly class="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-mono text-indigo-300 select-all">
          <button onclick="copyRawKey()" class="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-500">Copy</button>
        </div>
      </div>
      <div class="flex justify-end space-x-3 pt-3 border-t border-slate-800">
        <button onclick="useKeyInPlayground()" class="rounded-lg border border-indigo-500/40 bg-indigo-950/40 px-3.5 py-1.5 text-xs font-medium text-indigo-300 hover:bg-indigo-900/60">Use in Playground</button>
        <button onclick="closeSuccessModal()" class="rounded-lg bg-slate-800 px-4 py-2 text-xs text-white hover:bg-slate-700">Close</button>
      </div>
    </div>
  </div>

  <!-- Client-side Logic Script -->
  <script>
    let activeTab = 'routes';
    let rawGeneratedKey = '';

    function showToast(text, isError = false) {
      const el = document.getElementById('toast-banner');
      el.innerText = text;
      el.className = isError
        ? 'rounded-lg p-3 text-xs border bg-rose-950/40 text-rose-300 border-rose-800/60'
        : 'rounded-lg p-3 text-xs border bg-emerald-950/40 text-emerald-300 border-emerald-800/60';
      el.classList.remove('hidden');
      setTimeout(() => el.classList.add('hidden'), 5000);
    }

    function switchTab(tab) {
      activeTab = tab;
      ['routes', 'keys', 'playground'].forEach(t => {
        const sec = document.getElementById('tab-' + t);
        const btn = document.getElementById('tab-btn-' + t);
        if (t === tab) {
          sec.classList.remove('hidden');
          btn.className = 'flex items-center space-x-2 rounded-md px-3.5 py-1.5 font-medium transition bg-indigo-600 text-white shadow';
        } else {
          sec.classList.add('hidden');
          btn.className = 'flex items-center space-x-2 rounded-md px-3.5 py-1.5 font-medium transition text-slate-400 hover:text-white';
        }
      });
      if (tab === 'routes') loadRoutes();
      if (tab === 'keys') loadKeys();
    }

    async function loadOverview() {
      try {
        const res = await fetch('/admin/overview');
        if (!res.ok) return;
        const d = await res.json();
        document.getElementById('stat-routes-count').innerText = d.total_policies;
        document.getElementById('stat-hops-count').innerText = `(${d.total_routes} hops)`;
        document.getElementById('stat-keys-active').innerText = d.active_keys;
        document.getElementById('stat-keys-total').innerText = `active / ${d.total_keys} total`;
        
        const breakerEl = document.getElementById('stat-breaker-status');
        if (d.open_breakers_count > 0) {
          breakerEl.innerText = `${d.open_breakers_count} Tripped`;
          breakerEl.className = 'text-2xl font-bold text-rose-400';
        } else {
          breakerEl.innerText = 'All Healthy';
          breakerEl.className = 'text-2xl font-bold text-emerald-400';
        }

        if (d.live_gemini_configured) {
          document.getElementById('dot-gemini').className = 'h-1.5 w-1.5 rounded-full bg-emerald-400';
          document.getElementById('label-gemini').className = 'text-emerald-300 font-medium';
          document.getElementById('label-gemini').innerText = 'Gemini: Live BYOK';
        }
        if (d.live_openrouter_configured) {
          document.getElementById('dot-openrouter').className = 'h-1.5 w-1.5 rounded-full bg-emerald-400';
          document.getElementById('label-openrouter').className = 'text-emerald-300 font-medium';
          document.getElementById('label-openrouter').innerText = 'OpenRouter: Live BYOK';
        }
      } catch (e) {
        console.error('Failed to load overview:', e);
      }
    }

    async function loadRoutes() {
      const container = document.getElementById('policies-container');
      try {
        const res = await fetch('/admin/routes');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        const policies = data.data || [];

        container.innerHTML = policies.map(p => `
          <div class="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40 shadow-sm">
            <div class="flex items-center justify-between border-b border-slate-800 bg-slate-900/70 px-5 py-3 text-xs">
              <div class="flex items-center space-x-3">
                <span class="font-mono text-base font-bold text-white">${p.alias}</span>
                <span class="rounded bg-slate-800 px-2 py-0.5 text-slate-300 font-mono">max_retries: ${p.max_retries}</span>
              </div>
              <span class="text-slate-400 font-mono">timeout: ${p.timeout_ms}ms</span>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs text-slate-300">
                <thead class="border-b border-slate-800 bg-slate-950/40 uppercase tracking-wider text-slate-400">
                  <tr>
                    <th class="px-5 py-3 font-medium">Priority</th>
                    <th class="px-5 py-3 font-medium">Provider</th>
                    <th class="px-5 py-3 font-medium">Upstream Model</th>
                    <th class="px-5 py-3 font-medium">Route Key</th>
                    <th class="px-5 py-3 font-medium">Breaker State</th>
                    <th class="px-5 py-3 text-right font-medium">Simulation</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60">
                  ${p.routes.map(r => `
                    <tr class="hover:bg-slate-800/30">
                      <td class="px-5 py-3 font-mono font-bold">P${r.priority}</td>
                      <td class="px-5 py-3 font-medium text-white">${r.provider_name} <span class="text-[10px] text-slate-500 uppercase">(${r.provider_type})</span></td>
                      <td class="px-5 py-3 font-mono text-slate-300">${r.upstream_model}</td>
                      <td class="px-5 py-3 font-mono text-slate-400 text-[11px]">${r.route_key}</td>
                      <td class="px-5 py-3">
                        <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                          r.breaker_state === 'CLOSED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : r.breaker_state === 'OPEN'
                            ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 animate-pulse'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }">${r.breaker_state}</span>
                      </td>
                      <td class="px-5 py-3 text-right">
                        ${r.breaker_state === 'OPEN'
                          ? `<button onclick="resetBreakerAction('${r.route_key}')" class="rounded bg-emerald-600/80 px-2.5 py-1 text-xs text-white hover:bg-emerald-600">Reset Breaker</button>`
                          : `<button onclick="tripBreakerAction('${r.route_key}')" class="rounded border border-rose-800/60 bg-rose-950/40 px-2.5 py-1 text-xs text-rose-300 hover:bg-rose-900/60">Simulate Trip</button>`
                        }
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
        `).join('');
      } catch (e) {
        container.innerHTML = `<div class="p-4 text-xs text-rose-400">Failed to load routes: ${e.message}</div>`;
      }
    }

    async function resetBreakerAction(routeKey) {
      try {
        const res = await fetch('/admin/breaker/reset', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({route_key: routeKey})
        });
        const data = await res.json();
        showToast(data.message);
        loadRoutes();
        loadOverview();
      } catch (e) {
        showToast(e.message, true);
      }
    }

    async function tripBreakerAction(routeKey) {
      try {
        const res = await fetch('/admin/breaker/trip', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({route_key: routeKey})
        });
        const data = await res.json();
        showToast(data.message);
        loadRoutes();
        loadOverview();
      } catch (e) {
        showToast(e.message, true);
      }
    }

    async function loadKeys() {
      const tbody = document.getElementById('keys-table-body');
      try {
        const res = await fetch('/admin/keys');
        const d = await res.json();
        const keys = d.data || [];
        if (keys.length === 0) {
          tbody.innerHTML = '<tr><td colspan="7" class="px-5 py-6 text-center text-slate-500">No keys generated yet.</td></tr>';
          return;
        }
        tbody.innerHTML = keys.map(k => `
          <tr class="hover:bg-slate-800/30">
            <td class="px-5 py-3 font-medium text-white">${k.tenant}</td>
            <td class="px-5 py-3 font-mono text-slate-300">${k.key_prefix}...</td>
            <td class="px-5 py-3"><span class="rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-300">${k.rate_limit_rpm} RPM</span></td>
            <td class="px-5 py-3"><span class="rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-300">${k.max_concurrency} inflight</span></td>
            <td class="px-5 py-3">
              <span class="inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-bold ${k.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400'}">
                ${k.is_active ? 'ACTIVE' : 'REVOKED'}
              </span>
            </td>
            <td class="px-5 py-3 text-slate-400">${k.created_at ? new Date(k.created_at).toLocaleDateString() : '-'}</td>
            <td class="px-5 py-3 text-right">
              ${k.is_active ? `<button onclick="revokeKeyAction('${k.id}')" class="rounded border border-rose-800/60 bg-rose-950/40 px-2 py-1 text-xs text-rose-300 hover:bg-rose-900/60">Revoke</button>` : ''}
            </td>
          </tr>
        `).join('');
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-xs text-rose-400">Failed to load keys: ${e.message}</td></tr>`;
      }
    }

    function openCreateKeyModal() { document.getElementById('modal-create-key').classList.remove('hidden'); }
    function closeCreateKeyModal() { document.getElementById('modal-create-key').classList.add('hidden'); }
    function closeSuccessModal() { document.getElementById('modal-key-success').classList.add('hidden'); }

    async function submitCreateKey() {
      const tenant = document.getElementById('input-tenant').value.trim();
      const rpm = parseInt(document.getElementById('input-rpm').value) || 60;
      const conc = parseInt(document.getElementById('input-concurrency').value) || 10;
      if (!tenant) { alert('Tenant name is required.'); return; }

      try {
        const res = await fetch('/admin/keys', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ tenant, rate_limit_rpm: rpm, max_concurrency: conc })
        });
        const data = await res.json();
        closeCreateKeyModal();
        rawGeneratedKey = data.key;
        document.getElementById('success-key-token').value = data.key;
        document.getElementById('modal-key-success').classList.remove('hidden');
        loadKeys();
        loadOverview();
      } catch (e) {
        alert(e.message);
      }
    }

    function copyRawKey() {
      navigator.clipboard.writeText(rawGeneratedKey);
      showToast('API key copied to clipboard!');
    }

    function useKeyInPlayground() {
      document.getElementById('play-key').value = rawGeneratedKey;
      closeSuccessModal();
      switchTab('playground');
    }

    async function revokeKeyAction(keyId) {
      if (!confirm('Are you sure you want to revoke this API key?')) return;
      try {
        await fetch(`/admin/keys/${keyId}/revoke`, { method: 'POST' });
        showToast('API key revoked successfully.');
        loadKeys();
        loadOverview();
      } catch (e) {
        showToast(e.message, true);
      }
    }

    async function sendInference() {
      const key = document.getElementById('play-key').value.trim();
      const model = document.getElementById('play-model').value;
      const prompt = document.getElementById('play-prompt').value.trim();
      const system = document.getElementById('play-system').value.trim();
      const stream = document.getElementById('play-stream').checked;
      const out = document.getElementById('play-output');
      const diagBox = document.getElementById('diag-headers-box');
      const btn = document.getElementById('btn-send');
      const statusInd = document.getElementById('play-status-indicator');

      if (!key) { alert('Please enter your Gateway API key.'); return; }
      if (!prompt) { alert('Prompt is empty.'); return; }

      btn.disabled = true;
      btn.innerText = 'Inferencing...';
      statusInd.innerText = 'Connecting...';
      out.innerText = '';
      diagBox.classList.add('hidden');

      const messages = [];
      if (system) messages.push({ role: 'system', content: system });
      messages.push({ role: 'user', content: prompt });

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
        document.getElementById('diag-provider').innerText = res.headers.get('X-CRouter-Provider-Selected') || '—';
        document.getElementById('diag-model').innerText = res.headers.get('X-CRouter-Model-Selected') || '—';
        document.getElementById('diag-attempts').innerText = res.headers.get('X-CRouter-Attempts') || '1';
        document.getElementById('diag-gw-latency').innerText = (res.headers.get('X-CRouter-Latency-Gateway-Ms') || '—') + ' ms';
        document.getElementById('diag-up-latency').innerText = (res.headers.get('X-CRouter-Latency-Upstream-Ms') || '—') + ' ms';
        document.getElementById('diag-req-id').innerText = res.headers.get('X-CRouter-Request-ID') || '—';
        diagBox.classList.remove('hidden');

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error?.message || `HTTP ${res.status}`);
        }

        if (!stream) {
          const data = await res.json();
          out.innerText = data.choices?.[0]?.message?.content || '';
          statusInd.innerText = 'Completed (200 OK)';
        } else {
          statusInd.innerText = 'Streaming tokens...';
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let acc = '';
          let buf = '';
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += decoder.decode(value, { stream: true });
            const lines = buf.split('\\n');
            buf = lines.pop() || '';
            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed.startsWith('data:')) continue;
              const dataStr = trimmed.slice(5).trim();
              if (dataStr === '[DONE]') continue;
              try {
                const parsed = JSON.parse(dataStr);
                const delta = parsed.choices?.[0]?.delta?.content || '';
                if (delta) {
                  acc += delta;
                  out.innerText = acc;
                }
              } catch(e) {}
            }
          }
          statusInd.innerText = 'Stream Finished [DONE]';
        }
      } catch (err) {
        out.innerText = 'Error: ' + err.message;
        statusInd.innerText = 'Failed';
      } finally {
        btn.disabled = false;
        btn.innerText = 'Send Request';
        loadOverview();
      }
    }

    // Initialize
    loadOverview();
    loadRoutes();
    loadKeys();
  </script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the interactive CRouter Web Dashboard."""
    return DASHBOARD_HTML


@router.get("/", response_class=HTMLResponse)
async def serve_root():
    """Root endpoint serving the interactive CRouter Web Dashboard."""
    return DASHBOARD_HTML
