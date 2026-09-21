# CRouter — Multi-Provider AI Inference Gateway

> **"One Gateway. Every Model."**  
> *Self-hosted, open-source AI inference gateway engineered for intelligent routing, resilience, zero-token local testing, and observability.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Container-Docker_Compose-2496ED.svg?logo=docker&logoColor=white)](infra/compose/docker-compose.yml)

---

## 🎯 Highlights

- **OpenAI-Compatible Drop-In:** Works with standard OpenAI SDKs and clients via `POST /v1/chat/completions` (JSON & SSE streaming).
- **Multi-Provider Priority Routing:** Route by virtual alias (`auto/coding`, `mock-default`) across Mock, Google Gemini, and OpenRouter with automatic pre-stream failover.
- **Zero-Budget MVP (Rp0):** Run 100% locally with deterministic mock providers, simulated 429/503 faults, and artificial latency. Zero paid token usage required.
- **Distributed Rate & Concurrency Governance:** Redis-backed sliding-window rate limiting and in-flight connection leasing.
- **Resilience Engine:** Circuit breakers (`CLOSED`, `OPEN`, `HALF-OPEN`) and safe pre-stream retries with zero mid-stream corruption.
- **Security & Privacy First:** SHA-256 hashed API keys. Zero prompt or response token persistence in databases, logs, or traces.

---

## 🏗️ Architecture

```
                        ┌───────────────────────────────────┐
                        │        Client Application         │
                        │   (Curl / OpenAI SDK / SDLCraft)  │
                        └─────────────────┬─────────────────┘
                                          │ HTTP / SSE
                        ┌─────────────────▼─────────────────┐
                        │          CRouter Gateway          │
                        │       FastAPI Core Engine         │
                        └────────┬───────┬────────┬─────────┘
                                 │       │        │
            ┌────────────────────┘       │        └────────────────────┐
            ▼                            ▼                             ▼
  ┌───────────────────┐        ┌───────────────────┐         ┌───────────────────┐
  │    PostgreSQL     │        │   Redis 7.0+      │         │   OTel & Prom     │
  │  Metadata Store   │        │ Rate/Concurrency  │         │ (Traces, Metrics) │
  │ (Keys, Policies)  │        │ Circuit Breakers  │         │                   │
  └───────────────────┘        └───────────────────┘         └───────────────────┘
                                         │
                           ┌─────────────┴─────────────┐
                           │   Provider Adapter Layer  │
                           └─────┬───────────────┬─────┘
                                 │               │
               ┌─────────────────┴─┐           ┌─┴─────────────────┐
               ▼                   ▼           ▼                   ▼
       ┌───────────────┐   ┌───────────────┐ ┌───────────────┐   ┌───────────────┐
       │ Gemini Direct │   │  OpenRouter   │ │ Mock Engine A │   │ Mock Engine B │
       │  (Live API)   │   │  (Live API)   │ │  (Local Rp0)  │   │  (Local Rp0)  │
       └───────────────┘   └───────────────┘ └───────────────┘   └───────────────┘
```

---

## 🚀 Quickstart (Rp0 Zero-Budget Demo)

### 1. Start Infrastructure via Docker Compose
```bash
cp .env.example .env
docker compose -f infra/compose/docker-compose.yml up --build -d
```

### 2. Generate a Gateway API Key
```bash
docker compose -f infra/compose/docker-compose.yml exec gateway \
  crouter keys create --tenant "demo-agent" --rate-limit 60 --concurrency 5
```
Output:
```text
Generated Key: cr_live_a1b2c3d4e5f6... (Save this key! Raw key is shown only once)
```

### 3. Send Chat Completion
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <YOUR_GENERATED_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto/coding",
    "messages": [{"role": "user", "content": "Hello CRouter!"}],
    "stream": false
  }'
```

### 4. Test Automated Failover
```bash
# Inject 503 fault on mock-a
curl -X POST http://localhost:8001/mock/inject-fault?status=503&target=mock-a

# Gateway will automatically route to mock-b seamlessly!
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <YOUR_GENERATED_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto/coding",
    "messages": [{"role": "user", "content": "Test failover"}],
    "stream": false
  }'
# Check header: X-CRouter-Provider-Selected: mock-b
```

---

## 🖥️ Web Dashboard (Next.js / Tailwind CSS)

CRouter provides an interactive visual dashboard for gateway operators and developers:
- **Routes & Circuit Breaker Monitoring:** Real-time visibility into model aliases (`auto/coding`, `fast/chat`), provider health, and breaker states (`CLOSED`, `OPEN`, `HALF-OPEN`) with manual trip/reset simulations.
- **API Key Management:** Issue tenant-scoped API keys with sliding-window RPM limits, view key hashes, and revoke active keys.
- **Inference Playground:** Test completions directly in the browser with SSE streaming toggle and live diagnostic headers (`X-CRouter-Provider-Selected`, `X-CRouter-Latency-Gateway-Ms`, etc.).

### Accessing the Dashboard:
1. **Direct Gateway UI:** Navigate to `http://localhost:8000/dashboard` (or root `http://localhost:8000/`).
2. **Next.js Standalone Frontend:** Located in `apps/dashboard/`:
   ```bash
   cd apps/dashboard
   npm run dev
   # Open http://localhost:3000
   ```

---

## ⚡ Live Traffic Experimentation (BYOK)

CRouter operates strictly in **Rp0 Local Mock Mode** by default. To experiment with real AI models:

1. **Google Gemini:** Set `GEMINI_API_KEY` in `.env` (Free tier from [Google AI Studio](https://aistudio.google.com/)).
2. **OpenRouter:** Set `OPENROUTER_API_KEY` in `.env` (Access to 200+ models from [OpenRouter](https://openrouter.ai/keys)).

### Run Live Smoke Test Harness:
```bash
# Safely verifies live endpoints if keys are present, or falls back to Rp0 local mocks:
python scripts/smoke_test_live.py

# Or test specific providers:
python scripts/smoke_test_live.py --provider gemini
python scripts/smoke_test_live.py --provider openrouter
```

---

## 📡 Gateway Admin REST API

In addition to the CLI, CRouter provides REST administration endpoints under `/admin`:
- `GET /admin/overview` — High-level telemetry, key counts, route health, and BYOK status.
- `GET /admin/routes` — Active routing policies, priority fallback chains, and real-time breaker states.
- `POST /admin/breaker/reset` — Reset a tripped circuit breaker for a route.
- `POST /admin/breaker/trip` — Force-trip a circuit breaker for chaos testing.
- `GET /admin/keys` — List all registered API keys and tenant quotas.
- `POST /admin/keys` — Create a new API key (returns raw key once).
- `POST /admin/keys/{id}/revoke` — Revoke an active API key.

---

## 💻 CLI Usage

```bash
# Create key
crouter keys create --tenant "sdcraft" --rate-limit 120 --concurrency 10

# List keys
crouter keys list

# Revoke key
crouter keys revoke <key_prefix>
```

---

## 🧪 Testing

```bash
# Run complete test suite locally (38 tests)
python -m pytest
```

---

## 📄 License

CRouter is licensed under the [MIT License](LICENSE).

