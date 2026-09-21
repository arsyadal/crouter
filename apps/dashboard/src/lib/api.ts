export interface OverviewData {
  total_keys: number;
  active_keys: number;
  total_policies: number;
  total_routes: number;
  open_breakers_count: number;
  total_requests: number;
  avg_duration_ms: number;
  gateway_version: string;
  live_gemini_configured: boolean;
  live_openrouter_configured: boolean;
  live_commandcode_configured?: boolean;
}

export interface RouteDetail {
  id: string;
  provider_name: string;
  provider_type: string;
  upstream_model: string;
  priority: number;
  is_enabled: boolean;
  route_key: string;
  breaker_state: "CLOSED" | "OPEN" | "HALF_OPEN";
}

export interface PolicyDetail {
  id: string;
  alias: string;
  description?: string;
  max_retries: number;
  timeout_ms: number;
  routes: RouteDetail[];
}

export interface KeyItem {
  id: string;
  tenant: string;
  key_prefix: string;
  rate_limit_rpm: number;
  max_concurrency: number;
  is_active: boolean;
  revoked_at?: string | null;
  created_at: string;
}

export interface KeyCreateResult {
  id: string;
  tenant: string;
  key: string;
  key_prefix: string;
  rate_limit_rpm: number;
  max_concurrency: number;
  created_at: string;
}

export interface DiagnosticHeaders {
  requestId?: string;
  providerSelected?: string;
  modelSelected?: string;
  attempts?: string;
  latencyGatewayMs?: string;
  latencyUpstreamMs?: string;
}

export interface ChatMessageItem {
  role: "system" | "user" | "assistant";
  content: string;
}

export const GATEWAY_BASE =
  process.env.NEXT_PUBLIC_GATEWAY_URL ||
  (typeof window !== "undefined"
    ? window.location.hostname === "localhost"
      ? "http://localhost:8000"
      : ""
    : "http://localhost:8000");

export async function getOverview(): Promise<OverviewData> {
  const res = await fetch(`${GATEWAY_BASE}/admin/overview`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch overview: HTTP ${res.status}`);
  return res.json();
}

export async function getRoutes(): Promise<PolicyDetail[]> {
  const res = await fetch(`${GATEWAY_BASE}/admin/routes`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch routes: HTTP ${res.status}`);
  const json = await res.json();
  return json.data || [];
}

export async function getKeys(): Promise<KeyItem[]> {
  const res = await fetch(`${GATEWAY_BASE}/admin/keys`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch API keys: HTTP ${res.status}`);
  const json = await res.json();
  return json.data || [];
}

export async function createKey(params: {
  tenant: string;
  rate_limit_rpm?: number;
  max_concurrency?: number;
  key?: string;
}): Promise<KeyCreateResult> {
  const res = await fetch(`${GATEWAY_BASE}/admin/keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || err.detail || `Failed to create key: HTTP ${res.status}`);
  }
  return res.json();
}

export async function revokeKey(keyId: string): Promise<KeyItem> {
  const res = await fetch(`${GATEWAY_BASE}/admin/keys/${keyId}/revoke`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to revoke key: HTTP ${res.status}`);
  return res.json();
}

export async function resetBreaker(routeKey: string): Promise<{ route_key: string; breaker_state: string; message: string }> {
  const res = await fetch(`${GATEWAY_BASE}/admin/breaker/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ route_key: routeKey }),
  });
  if (!res.ok) throw new Error(`Failed to reset breaker: HTTP ${res.status}`);
  return res.json();
}

export async function tripBreaker(routeKey: string): Promise<{ route_key: string; breaker_state: string; message: string }> {
  const res = await fetch(`${GATEWAY_BASE}/admin/breaker/trip`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ route_key: routeKey }),
  });
  if (!res.ok) throw new Error(`Failed to trip breaker: HTTP ${res.status}`);
  return res.json();
}

export async function getHealthLive(): Promise<boolean> {
  try {
    const res = await fetch(`${GATEWAY_BASE}/health/live`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function getHealthReady(): Promise<boolean> {
  try {
    const res = await fetch(`${GATEWAY_BASE}/health/ready`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function executeInference(params: {
  apiKey: string;
  model: string;
  messages: ChatMessageItem[];
  stream: boolean;
  temperature: number;
  max_tokens: number;
  onChunk?: (text: string) => void;
  onHeaders?: (headers: DiagnosticHeaders) => void;
}): Promise<{ text: string; headers: DiagnosticHeaders; usage?: any }> {
  const headersObj: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${params.apiKey}`,
  };

  const payload = {
    model: params.model,
    messages: params.messages,
    stream: params.stream,
    temperature: params.temperature,
    max_tokens: params.max_tokens,
  };

  const res = await fetch(`${GATEWAY_BASE}/v1/chat/completions`, {
    method: "POST",
    headers: headersObj,
    body: JSON.stringify(payload),
  });

  const diagnosticHeaders: DiagnosticHeaders = {
    requestId: res.headers.get("X-CRouter-Request-ID") || undefined,
    providerSelected: res.headers.get("X-CRouter-Provider-Selected") || undefined,
    modelSelected: res.headers.get("X-CRouter-Model-Selected") || undefined,
    attempts: res.headers.get("X-CRouter-Attempts") || undefined,
    latencyGatewayMs: res.headers.get("X-CRouter-Latency-Gateway-Ms") || undefined,
    latencyUpstreamMs: res.headers.get("X-CRouter-Latency-Upstream-Ms") || undefined,
  };

  if (params.onHeaders) {
    params.onHeaders(diagnosticHeaders);
  }

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    const msg = errBody.error?.message || `HTTP ${res.status}: ${res.statusText}`;
    throw new Error(msg);
  }

  if (!params.stream) {
    const data = await res.json();
    const content = data.choices?.[0]?.message?.content || "";
    return { text: content, headers: diagnosticHeaders, usage: data.usage };
  }

  // Handle SSE streaming
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response stream body available");

  const decoder = new TextDecoder();
  let accumulatedText = "";
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data:")) continue;
      const dataContent = trimmed.replace(/^data:\s*/, "");
      if (dataContent === "[DONE]") continue;

      try {
        const parsed = JSON.parse(dataContent);
        const delta = parsed.choices?.[0]?.delta?.content || "";
        if (delta) {
          accumulatedText += delta;
          if (params.onChunk) {
            params.onChunk(accumulatedText);
          }
        }
      } catch {
        // ignore parse errors for partial json chunks
      }
    }
  }

  return { text: accumulatedText, headers: diagnosticHeaders };
}
