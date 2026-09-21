"use client";

import React, { useState, useEffect } from "react";
import { executeInference, DiagnosticHeaders, KeyItem } from "@/lib/api";
import {
  Send,
  Sliders,
  Terminal,
  Activity,
  Zap,
  Clock,
  Radio,
  Check,
  AlertCircle,
  Sparkles,
} from "lucide-react";

interface ChatPlaygroundProps {
  keys: KeyItem[];
  defaultKey?: string;
}

export function ChatPlayground({ keys, defaultKey }: ChatPlaygroundProps) {
  const [apiKey, setApiKey] = useState<string>(defaultKey || "");
  const [model, setModel] = useState<string>("auto/coding");
  const [systemPrompt, setSystemPrompt] = useState<string>(
    "You are a helpful platform engineering AI assistant running through CRouter."
  );
  const [userPrompt, setUserPrompt] = useState<string>(
    "Explain why a circuit breaker pattern is essential for multi-provider AI inference."
  );
  const [stream, setStream] = useState<boolean>(true);
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(256);

  // Sync defaultKey when prop changes (e.g. key created in modal)
  useEffect(() => {
    if (defaultKey) {
      setApiKey(defaultKey);
    }
  }, [defaultKey]);

  // Execution states
  const [loading, setLoading] = useState<boolean>(false);
  const [responseContent, setResponseContent] = useState<string>("");
  const [diagnosticHeaders, setDiagnosticHeaders] = useState<DiagnosticHeaders | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ totalTimeMs?: number; tokens?: any }>({});

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) {
      setError("Please provide a valid Gateway Bearer API key.");
      return;
    }
    if (!userPrompt.trim()) {
      setError("User prompt cannot be empty.");
      return;
    }

    setLoading(true);
    setError(null);
    setResponseContent("");
    setDiagnosticHeaders(null);
    const startTime = performance.now();

    try {
      const messages: { role: "system" | "user"; content: string }[] = [];
      if (systemPrompt.trim()) {
        messages.push({ role: "system", content: systemPrompt.trim() });
      }
      messages.push({ role: "user", content: userPrompt.trim() });

      const result = await executeInference({
        apiKey: apiKey.trim(),
        model: model.trim(),
        messages,
        stream,
        temperature,
        max_tokens: maxTokens,
        onChunk: (chunkText) => {
          setResponseContent(chunkText);
        },
        onHeaders: (headers) => {
          setDiagnosticHeaders(headers);
        },
      });

      const totalTime = Math.round(performance.now() - startTime);
      setStats({ totalTimeMs: totalTime, tokens: result.usage });
      setResponseContent(result.text);
      if (result.headers) {
        setDiagnosticHeaders(result.headers);
      }
    } catch (err: any) {
      setError(err.message || "Inference call failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-white">
          Interactive Inference Playground
        </h2>
        <p className="text-sm text-slate-400">
          Dispatch requests directly to CRouter gateway, test streaming SSE, and inspect diagnostic headers in real time.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Configuration Controls (5 cols) */}
        <div className="space-y-4 lg:col-span-5">
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 shadow-sm">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
              <Sliders className="h-4 w-4 text-indigo-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Gateway Parameters
              </h3>
            </div>

            <div className="mt-4 space-y-4">
              {/* API Key */}
              <div>
                <label className="block text-xs font-medium text-slate-300">
                  Gateway API Key (Bearer)
                </label>
                <input
                  type="password"
                  placeholder="cr_live_..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-mono text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
                {keys.length > 0 && (
                  <p className="mt-1 text-[11px] text-slate-400">
                    Active tenants detected:{" "}
                    {keys.slice(0, 3).map((k) => (
                      <span
                        key={k.id}
                        className="mr-1 rounded bg-slate-800 px-1 py-0.5 text-slate-300 font-mono text-[10px]"
                      >
                        {k.tenant}
                      </span>
                    ))}
                  </p>
                )}
              </div>

              {/* Model Alias */}
              <div>
                <label className="block text-xs font-medium text-slate-300">
                  Model Alias / Target
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="auto/coding">auto/coding (Priority: mock-a → mock-b)</option>
                  <option value="fast/chat">fast/chat (Priority: gemini → openrouter → mock-a)</option>
                  <option value="mock-a">mock-a (Deterministic Mock A)</option>
                  <option value="mock-b">mock-b (Deterministic Mock B)</option>
                  <option value="gemini-1.5-flash">gemini-1.5-flash (Google Gemini Direct)</option>
                  <option value="openrouter/meta-llama/llama-3.2-3b-instruct:free">
                    openrouter/llama-3.2-3b-instruct:free (OpenRouter)
                  </option>
                </select>
              </div>

              {/* SSE Stream Toggle */}
              <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                <div>
                  <span className="text-xs font-medium text-white">SSE Streaming</span>
                  <p className="text-[11px] text-slate-400">
                    Stream tokens chunk-by-chunk via Server-Sent Events
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setStream(!stream)}
                  className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    stream ? "bg-indigo-600" : "bg-slate-700"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      stream ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Temperature */}
              <div>
                <div className="flex justify-between text-xs text-slate-300">
                  <span>Temperature</span>
                  <span className="font-mono text-indigo-400">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="mt-1 w-full accent-indigo-500"
                />
              </div>

              {/* Max Tokens */}
              <div>
                <div className="flex justify-between text-xs text-slate-300">
                  <span>Max Tokens</span>
                  <span className="font-mono text-indigo-400">{maxTokens}</span>
                </div>
                <input
                  type="range"
                  min="16"
                  max="2048"
                  step="16"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="mt-1 w-full accent-indigo-500"
                />
              </div>

              {/* System Prompt */}
              <div>
                <label className="block text-xs font-medium text-slate-300">
                  System Prompt (Optional)
                </label>
                <textarea
                  rows={2}
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Prompt Input & Output (7 cols) */}
        <div className="space-y-4 lg:col-span-7">
          {/* User Input Card */}
          <form
            onSubmit={handleSend}
            className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 shadow-sm"
          >
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
              User Message
            </label>
            <textarea
              rows={3}
              required
              placeholder="Ask a question or provide instructions..."
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
            <div className="mt-3 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Endpoint: <code className="text-indigo-300">POST /v1/chat/completions</code>
              </span>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center space-x-2 rounded-lg bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Sparkles className="h-4 w-4 animate-spin text-white" />
                    <span>Inferencing...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    <span>Send Request</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Error Message */}
          {error && (
            <div className="rounded-xl border border-rose-800/60 bg-rose-950/40 p-4 text-xs text-rose-300 flex items-start space-x-2">
              <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
              <div>
                <strong className="font-semibold">Gateway Error:</strong> {error}
              </div>
            </div>
          )}

          {/* Diagnostic Headers Card */}
          {diagnosticHeaders && (
            <div className="rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-4 text-xs">
              <div className="flex items-center space-x-2 pb-2 border-b border-indigo-500/20 text-indigo-300 font-bold uppercase tracking-wider text-[11px]">
                <Activity className="h-4 w-4" />
                <span>Response Diagnostics (X-CRouter Headers)</span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] uppercase text-slate-400 block">
                    Provider Selected
                  </span>
                  <span className="font-bold text-white text-xs">
                    {diagnosticHeaders.providerSelected || "—"}
                  </span>
                </div>
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] uppercase text-slate-400 block">
                    Upstream Model
                  </span>
                  <span className="font-mono text-slate-200 text-xs">
                    {diagnosticHeaders.modelSelected || "—"}
                  </span>
                </div>
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] uppercase text-slate-400 block">
                    Attempts / Hops
                  </span>
                  <span className="font-bold text-emerald-400 text-xs">
                    {diagnosticHeaders.attempts || "1"}
                  </span>
                </div>
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] uppercase text-slate-400 block">
                    Gateway Latency
                  </span>
                  <span className="font-mono text-cyan-300 text-xs">
                    {diagnosticHeaders.latencyGatewayMs ? `${diagnosticHeaders.latencyGatewayMs} ms` : "—"}
                  </span>
                </div>
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] uppercase text-slate-400 block">
                    Upstream Latency
                  </span>
                  <span className="font-mono text-indigo-300 text-xs">
                    {diagnosticHeaders.latencyUpstreamMs ? `${diagnosticHeaders.latencyUpstreamMs} ms` : "—"}
                  </span>
                </div>
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] uppercase text-slate-400 block">
                    Request Trace ID
                  </span>
                  <span className="font-mono text-[10px] text-slate-400 truncate block">
                    {diagnosticHeaders.requestId || "—"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Response Output Box */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950/60 px-4 py-2.5 text-xs text-slate-400">
              <div className="flex items-center space-x-2">
                <Terminal className="h-3.5 w-3.5 text-indigo-400" />
                <span className="font-medium text-slate-300">Completion Output</span>
              </div>
              {stats.totalTimeMs && (
                <div className="flex items-center space-x-2">
                  <Clock className="h-3 w-3 text-slate-400" />
                  <span>{stats.totalTimeMs}ms elapsed</span>
                </div>
              )}
            </div>
            <div className="min-h-[160px] p-4 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
              {loading && !responseContent ? (
                <div className="flex items-center space-x-2 text-indigo-400">
                  <Sparkles className="h-4 w-4 animate-spin" />
                  <span>Awaiting tokens from CRouter gateway...</span>
                </div>
              ) : responseContent ? (
                responseContent
              ) : (
                <span className="text-slate-600 italic">
                  Press &quot;Send Request&quot; to test completion output.
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
