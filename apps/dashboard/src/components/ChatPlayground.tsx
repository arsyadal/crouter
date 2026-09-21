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
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

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
        <h2 className="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          Interactive Inference Playground
        </h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Dispatch requests directly to CRouter gateway, test streaming SSE, and inspect diagnostic headers in real time.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Configuration Controls (5 cols) */}
        <div className="space-y-4 lg:col-span-5">
          <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm space-y-4 text-xs dark:border-zinc-800 dark:bg-zinc-900/50">
            <div className="flex items-center space-x-2 border-b border-zinc-200 pb-3 dark:border-zinc-800">
              <Sliders className="h-4 w-4 text-zinc-500 dark:text-zinc-400" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
                Gateway Parameters
              </h3>
            </div>

            <div className="mt-4 space-y-4">
              {/* API Key */}
              <div>
                <label className="block font-medium text-zinc-700 dark:text-zinc-300">
                  Gateway API Key (Bearer)
                </label>
                <input
                  type="password"
                  placeholder="cr_live_..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs font-mono text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-500 transition-colors"
                />
                {keys.length > 0 && (
                  <p className="mt-1 text-[11px] text-zinc-500 dark:text-zinc-400">
                    Active tenants detected:{" "}
                    {keys.slice(0, 3).map((k) => (
                      <span
                        key={k.id}
                        className="mr-1 rounded-full border border-zinc-200 bg-zinc-100 px-2 py-0.5 text-zinc-700 font-mono text-[10px] dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                      >
                        {k.tenant}
                      </span>
                    ))}
                  </p>
                )}
              </div>

              {/* Model Alias */}
              <div>
                <label className="block font-medium text-zinc-700 dark:text-zinc-300">
                  Model Alias / Target
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:border-zinc-500 transition-colors"
                >
                  <option value="auto/coding">auto/coding (CommandCode Real Upstream: DeepSeek / Ling)</option>
                  <option value="fast/chat">fast/chat (CommandCode → Gemini → OpenRouter)</option>
                  <option value="commandcode/deepseek/deepseek-v4-flash">commandcode/deepseek/deepseek-v4-flash</option>
                  <option value="commandcode/inclusionai/ling-3.0-flash-sante:free">commandcode/inclusionai/ling-3.0-flash-sante:free</option>
                  <option value="mock-default">mock-default (Deterministic Mock A → Mock B)</option>
                  <option value="mock-a">mock-a (Deterministic Mock A)</option>
                  <option value="mock-b">mock-b (Deterministic Mock B)</option>
                  <option value="gemini-1.5-flash">gemini-1.5-flash (Google Gemini Direct)</option>
                  <option value="openrouter/meta-llama/llama-3.2-3b-instruct:free">
                    openrouter/llama-3.2-3b-instruct:free (OpenRouter)
                  </option>
                </select>
              </div>

              {/* SSE Stream Toggle */}
              <div className="flex items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950/60">
                <div>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">SSE Streaming</span>
                  <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                    Stream tokens chunk-by-chunk via Server-Sent Events
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setStream(!stream)}
                  className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    stream ? "bg-zinc-900 dark:bg-zinc-100" : "bg-zinc-300 dark:bg-zinc-700"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-4 w-4 transform rounded-full shadow ring-0 transition duration-200 ease-in-out ${
                      stream
                        ? "translate-x-5 bg-white dark:bg-zinc-900"
                        : "translate-x-0 bg-white"
                    }`}
                  />
                </button>
              </div>

              {/* Temperature */}
              <div>
                <div className="flex justify-between text-zinc-700 dark:text-zinc-300">
                  <span>Temperature</span>
                  <span className="font-mono text-zinc-900 dark:text-zinc-100 font-medium">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="mt-1 w-full accent-zinc-900 dark:accent-zinc-100 cursor-pointer"
                />
              </div>

              {/* Max Tokens */}
              <div>
                <div className="flex justify-between text-zinc-700 dark:text-zinc-300">
                  <span>Max Tokens</span>
                  <span className="font-mono text-zinc-900 dark:text-zinc-100 font-medium">{maxTokens}</span>
                </div>
                <input
                  type="range"
                  min="16"
                  max="2048"
                  step="16"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="mt-1 w-full accent-zinc-900 dark:accent-zinc-100 cursor-pointer"
                />
              </div>

              {/* System Prompt */}
              <div>
                <label className="block font-medium text-zinc-700 dark:text-zinc-300">
                  System Prompt (Optional)
                </label>
                <textarea
                  rows={2}
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-500 transition-colors"
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
            className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50"
          >
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              User Message
            </label>
            <textarea
              rows={3}
              required
              placeholder="Ask a question or provide instructions..."
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className="mt-2 w-full rounded-md border border-zinc-300 bg-white p-3 text-xs text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-500 transition-colors"
            />
            <div className="mt-3 flex items-center justify-between">
              <span className="text-[11px] text-zinc-500 dark:text-zinc-400">
                Endpoint: <code className="font-mono text-zinc-700 dark:text-zinc-300">POST /v1/chat/completions</code>
              </span>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center space-x-1.5 rounded-md bg-zinc-900 px-4 py-2 text-xs font-medium text-white shadow-sm hover:bg-zinc-800 transition dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Sparkles className="h-3.5 w-3.5 animate-spin" />
                    <span>Inferencing...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-3.5 w-3.5" />
                    <span>Send Request</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Gateway Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Diagnostic Headers Card */}
          {diagnosticHeaders && (
            <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-xs dark:border-zinc-800 dark:bg-zinc-950/60">
              <div className="flex items-center space-x-2 pb-2 border-b border-zinc-200 text-zinc-700 font-semibold uppercase tracking-wider text-[11px] dark:border-zinc-800 dark:text-zinc-300">
                <Activity className="h-3.5 w-3.5" />
                <span>Response Diagnostics (X-CRouter Headers)</span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                <div className="rounded-lg bg-white p-2.5 border border-zinc-200 shadow-sm dark:bg-zinc-900/60 dark:border-zinc-800">
                  <span className="text-[10px] uppercase text-zinc-500 dark:text-zinc-400 block">
                    Provider Selected
                  </span>
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100 text-xs">
                    {diagnosticHeaders.providerSelected || "-"}
                  </span>
                </div>
                <div className="rounded-lg bg-white p-2.5 border border-zinc-200 shadow-sm dark:bg-zinc-900/60 dark:border-zinc-800">
                  <span className="text-[10px] uppercase text-zinc-500 dark:text-zinc-400 block">
                    Upstream Model
                  </span>
                  <span className="font-mono text-zinc-800 dark:text-zinc-200 text-xs">
                    {diagnosticHeaders.modelSelected || "-"}
                  </span>
                </div>
                <div className="rounded-lg bg-white p-2.5 border border-zinc-200 shadow-sm dark:bg-zinc-900/60 dark:border-zinc-800">
                  <span className="text-[10px] uppercase text-zinc-500 dark:text-zinc-400 block">
                    Attempts / Hops
                  </span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400 text-xs font-mono">
                    {diagnosticHeaders.attempts || "1"}
                  </span>
                </div>
                <div className="rounded-lg bg-white p-2.5 border border-zinc-200 shadow-sm dark:bg-zinc-900/60 dark:border-zinc-800">
                  <span className="text-[10px] uppercase text-zinc-500 dark:text-zinc-400 block">
                    Gateway Latency
                  </span>
                  <span className="font-mono text-zinc-900 dark:text-zinc-100 text-xs font-semibold">
                    {diagnosticHeaders.latencyGatewayMs ? `${diagnosticHeaders.latencyGatewayMs} ms` : "-"}
                  </span>
                </div>
                <div className="rounded-lg bg-white p-2.5 border border-zinc-200 shadow-sm dark:bg-zinc-900/60 dark:border-zinc-800">
                  <span className="text-[10px] uppercase text-zinc-500 dark:text-zinc-400 block">
                    Upstream Latency
                  </span>
                  <span className="font-mono text-zinc-900 dark:text-zinc-100 text-xs font-semibold">
                    {diagnosticHeaders.latencyUpstreamMs ? `${diagnosticHeaders.latencyUpstreamMs} ms` : "-"}
                  </span>
                </div>
                <div className="rounded-lg bg-white p-2.5 border border-zinc-200 shadow-sm dark:bg-zinc-900/60 dark:border-zinc-800">
                  <span className="text-[10px] uppercase text-zinc-500 dark:text-zinc-400 block">
                    Request ID
                  </span>
                  <span className="font-mono text-[10px] text-zinc-500 dark:text-zinc-400 truncate block">
                    {diagnosticHeaders.requestId || "-"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Response Output Box */}
          <div className="rounded-xl border border-zinc-200 bg-white shadow-sm overflow-hidden dark:border-zinc-800 dark:bg-zinc-900/50">
            <div className="flex items-center justify-between border-b border-zinc-200 bg-zinc-50/70 px-4 py-2.5 text-xs text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950/60 dark:text-zinc-400">
              <div className="flex items-center space-x-2">
                <Terminal className="h-3.5 w-3.5 text-zinc-700 dark:text-zinc-300" />
                <span className="font-medium text-zinc-800 dark:text-zinc-200">Completion Output</span>
              </div>
              {stats.totalTimeMs && (
                <div className="flex items-center space-x-1.5 font-mono text-[11px]">
                  <Clock className="h-3 w-3 text-zinc-400" />
                  <span>{stats.totalTimeMs}ms elapsed</span>
                </div>
              )}
            </div>
            <div className="min-h-[160px] p-4 text-xs font-mono text-zinc-800 dark:text-zinc-200 whitespace-pre-wrap leading-relaxed">
              {loading && !responseContent ? (
                <div className="flex items-center space-x-2 text-zinc-500">
                  <Sparkles className="h-3.5 w-3.5 animate-spin" />
                  <span>Awaiting tokens from CRouter gateway...</span>
                </div>
              ) : responseContent ? (
                responseContent
              ) : (
                <span className="text-zinc-400 italic">
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
