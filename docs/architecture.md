# CRouter Architecture & Design Specification

## Overview

CRouter is an intelligent multi-provider AI inference gateway engineered for high-throughput resilience, pre-stream failover, zero-token local testing, and strict zero-prompt persistence.

## Core Modules

### 1. Gateway Core (`apps/gateway`)
- **FastAPI Engine:** Serves `/v1/chat/completions`, `/v1/models`, `/health/live`, `/health/ready`, and `/metrics`.
- **Authentication & Security:** Authenticates Bearer tokens using SHA-256 hashes (`key_hash`). The gateway never stores raw keys.
- **Fail-Closed Governance:** Rejects invalid or revoked keys before routing or upstream resource consumption.

### 2. Provider Adapter Layer (`packages/adapters`)
- **Abstract Adapter (`BaseProviderAdapter`):** Provides normalized interfaces: `map_request()`, `send_completion()`, `stream_completion()`, `map_error()`.
- **MockAdapter:** Connects to local deterministic mock providers.
- **GeminiAdapter:** REST API `v1beta` adapter for Google Gemini.
- **OpenRouterAdapter:** OpenAI-dialect adapter for OpenRouter.

### 3. Engine (`apps/gateway/engine`)
- **Router:** Resolves virtual aliases (e.g. `auto/coding`) into priority-ordered candidate chains.
- **Circuit Breaker:** State machine (`CLOSED`, `OPEN`, `HALF_OPEN`) tracking rolling failure thresholds.
- **Rate Limiter & Concurrency Leaser:** Redis sliding-window sorted-sets (`ZSET`) and in-flight lease counters.

### 4. Zero-Budget Mock Provider (`apps/mock_provider`)
- Provides fault injection endpoints (`/mock/inject-fault`, `/mock/reset`).
- Simulates arbitrary HTTP statuses (200, 429, 500, 503), latency delays, and chunk-by-chunk SSE streaming.
