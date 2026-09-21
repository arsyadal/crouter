# Product Requirements Document (PRD)

# CRouter — Multi-Provider AI Inference Gateway

> **"One Gateway. Every Model."**  
> *Self-hosted, open-source AI inference gateway designed for intelligent routing, resilience, zero-token local testing, and observability.*

---

| Metadata | Value |
|---|---|
| **Project Name** | **CRouter** |
| **Repository** | `github.com/arsyadal/crouter` |
| **Package / CLI** | `crouter` |
| **Docker Image** | `crouter/gateway:latest` |
| **API Base URL** | `http://localhost:8000/v1` |
| **Version** | 1.0 (MVP Specification) |
| **Status** | Approved for Implementation |
| **Date** | 2026-09-21 |
| **Owner** | Muhammad Arsyad (`arsyadal`) |
| **Target Budget** | **Rp0 (Zero Cash Outlay)** for complete MVP development and testing |
| **License** | Apache 2.0 / MIT (Open Source) |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals, Non-Goals, and Constraints](#3-goals-non-goals-and-constraints)
4. [Target Personas and User Stories](#4-target-personas-and-user-stories)
5. [Scope and Phased Release Plan](#5-scope-and-phased-release-plan)
6. [Core Architectural Workflows](#6-core-architectural-workflows)
7. [Functional Requirements](#7-functional-requirements)
8. [Public API Contract & Error Model](#8-public-api-contract--error-model)
9. [Technical Architecture & Component Design](#9-technical-architecture--component-design)
10. [Data Model & State Management](#10-data-model--state-management)
11. [Non-Functional Requirements (NFR)](#11-non-functional-requirements-nfr)
12. [Success Metrics & Verification Evidence](#12-success-metrics--evidence)
13. [Comprehensive Failure & Test Matrix](#13-comprehensive-failure--test-matrix)
14. [Repository & Directory Structure](#14-repository--directory-structure)
15. [Implementation Roadmap & Ticket Breakdown](#15-implementation-roadmap--ticket-breakdown)
16. [Risk Management & Mitigations](#16-risk-management--mitigations)
17. [Zero-Budget Development & Cost Policy](#17-zero-budget-development--cost-policy)
18. [Architecture Decision Records (ADR) & Defaults](#18-architecture-decision-records-adr--defaults)
19. [First-Run Acceptance Demo Script](#19-first-run-acceptance-demo-script)

---

## 1. Executive Summary

**CRouter** is a high-performance, self-hosted, OpenAI-compatible AI inference gateway engineered to act as a resilient single entry point for multi-provider AI model traffic. It sits between client applications (such as autonomous agents, developer tools, or platforms like SDLCraft) and upstream AI providers (such as Gemini, OpenRouter, and local mocks). 

CRouter addresses the operational challenges of building AI-backed applications: fragmented SDKs, brittle failure handling, rate limit exhaustion, lack of traffic visibility, and high developer costs during API integration testing.

CRouter is built from day one under a **strict Zero-Budget MVP philosophy (Modal Rp0)**:
- Full platform engineering capabilities—including routing, circuit breakers, rate limits, concurrency pooling, and distributed metrics—are developed, tested, and benchmarked locally using **deterministic mock providers**.
- Developers can execute 10,000+ test requests and failure simulations without consuming a single third-party API token or paying for cloud infrastructure.
- Designed as a centerpiece backend/platform engineering portfolio, proving mastery of async Python (FastAPI), distributed systems (Redis atomic primitives), relational modeling (PostgreSQL), telemetry (OpenTelemetry/Prometheus), and container orchestration.

### Product Thesis

> *"Applications should depend on a single immutable, standards-compliant inference endpoint. The gateway must own model routing, quota governance, failure recovery, and observability without ever handling raw model weights or compromising user data privacy."*

---

## 2. Problem Statement

Modern AI engineering teams face recurring systemic bottlenecks when integrating external Large Language Model APIs:

1. **SDK and Schema Fragmentation:** Every provider (OpenAI, Google Gemini, Anthropic, OpenRouter) has diverging parameter schemas, error payloads, and authentication lifecycles. Swapping models requires rewriting application code.
2. **Brittle Upstream Reliability:** Upstream AI providers frequently suffer transient 503 outages, sudden 429 quota throttles, network spikes, and silent drops. Applications crash without uniform retry and circuit-breaking logic.
3. **Expensive Development Feedback Loops:** Testing retry logic, rate limit handlers, and failover pathways using live AI endpoints burns paid token credits and exhausts free quotas within hours.
4. **Zero Traffic Visibility:** Teams lack centralized telemetry to track latency percentiles (p50/p95/p99), token consumption attribution, failure rates, and route health across disparate providers.
5. **No Tenant Isolation:** Multi-service internal environments risk "noisy neighbor" starvation, where one rogue process consumes the entire organization's rate quota.

**Consequence:** Engineering velocity degrades as developers spend more time managing provider quirks and debugging upstream failures than delivering product value.

---

## 3. Goals, Non-Goals, and Constraints

### 3.1 Primary Goals

| Goal ID | Objective | Description |
|---|---|---|
| **G1** | **OpenAI Compatibility** | Deliver a fully standard `POST /v1/chat/completions` endpoint supporting streaming (SSE) and non-streaming modes. |
| **G2** | **Multi-Provider Routing** | Route dynamically across at least two real providers (Gemini, OpenRouter) and built-in local deterministic mocks. |
| **G3** | **Pre-Stream Failover** | Automatically reroute failed requests (503, 429, timeouts) to fallback routes before downstream bytes are committed. |
| **G4** | **Distributed Rate & Concurrency Limits** | Enforce tenant/key request limits and concurrent in-flight leases across multiple gateway replicas using Redis. |
| **G5** | **Zero-Leak Telemetry** | Export OpenTelemetry traces and Prometheus metrics without logging prompt text, secrets, or unbounded customer PII. |
| **G6** | **Zero-Budget Local MVP** | Provide a turnkey `docker compose` stack runnable with Rp0 outlay on standard developer hardware. |
| **G7** | **Deterministic Benchmarking** | Provide reproducible k6/Locust load testing harnesses measuring pure gateway overhead vs. upstream mock baseline. |

### 3.2 Non-Goals for MVP

- **Serving Model Weights / Hosting GPUs:** CRouter routes inference requests; it does not host, fine-tune, or serve local model weights.
- **Full OpenAI Ecosystem Parity:** MVP explicitly focuses on Chat Completions (`/v1/chat/completions`) and Health endpoints. Assistants, Audio, Realtime, and Embeddings are deferred.
- **Mid-Stream Provider Migration:** If a provider drops connection *after* tokens have begun streaming to the client, CRouter safely aborts with an error rather than risking cross-provider text corruption.
- **Paid Token Resale / Billing Platform:** No credit card billing, stripe integrations, or consumer markup models. CRouter operates strictly as self-hosted enterprise/developer infrastructure.
- **Semantic Caching / Dynamic LLM Quality Scoring:** CRouter avoids unpredictable semantic similarity caching in MVP to maintain absolute determinism and zero prompt-privacy risk.

### 3.3 Operating Constraints

- **Bring-Your-Own-Key (BYOK):** The deployment operator supplies their own upstream provider keys. Provider credentials are never checked into Git or exposed via API.
- **Fail-Closed Security:** Unauthorized or revoked gateway keys must be rejected before any routing or resource allocation occurs.
- **Ephemeral Request Payload:** Prompt and completion texts are never written to database tables, logs, or metrics by default.

---

## 4. Target Personas and User Stories

### 4.1 Personas

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│   Backend / AI Dev      │     │    Platform / DevOps    │     │   Autonomous AI Agent   │
│ Consumes single API     │     │ Manages routes, quotas, │     │ (e.g. SDLCraft)         │
│ across multiple models  │     │ observability & uptime  │     │ Requires zero-downtime  │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

1. **Application / AI Developer:** Needs a reliable endpoint that mimics OpenAI syntax, so switching between Gemini, Claude, or open-source models requires only a single parameter change (`"model": "auto/coding"`).
2. **Platform & Reliability Engineer:** Needs visibility into error budgets, circuit breaker trips, latency heatmaps, and per-key usage quotas.
3. **Autonomous Coding Agent (SDLCraft):** Demands automated failover so long-running workflows do not fail mid-step due to upstream 503 errors.
4. **Open-Source Contributor / Recruiter:** Can clone the repository, run `docker compose up`, and verify 100% of the test suite without acquiring third-party API keys.

### 4.2 User Stories

- **US-01:** *As a developer*, I want to point my existing OpenAI Python SDK to `http://localhost:8000/v1` and receive valid completions without altering my prompt formatting.
- **US-02:** *As an agent pipeline*, when my primary Gemini route throws an upstream 503, I want CRouter to seamlessly dispatch the request to OpenRouter within milliseconds before emitting the first token.
- **US-03:** *As a platform administrator*, I want to set a rate limit of 60 requests/minute on a specific gateway API key, backed by Redis, so multiple replicas enforce the exact same ceiling.
- **US-04:** *As an open-source evaluator*, I want to simulate network jitter and upstream 429 rate limits locally via the mock provider to verify circuit breaker trip-and-reset mechanics.

---

## 5. Scope and Phased Release Plan

```
Phase 0: Foundation ──► Phase 1: MVP Core ──► Phase 2: Resilience ──► Phase 3: Telemetry ──► Phase 4: Platform
[Mock Engine + CI]       [FastAPI + 2 Adapters]   [Redis Limits + Failover]  [OTel + Prometheus]     [Kind K8s + k6 Load]
```

### Phase 0: Foundation & Zero-Token Mock Engine (Week 1)
- Repository setup, Python 3.12, UV / Poetry dependency management, Ruff linting, pytest.
- **Deterministic Mock Provider Service:** Configurable FastAPI mock service capable of simulating HTTP 200, 429, 500, 503, artificial latency delays, SSE token streaming, and network drops.
- Docker Compose baseline: Gateway, Postgres 16, Redis 7, Mock Provider.
- CI pipeline running lint, type checks, and mock unit tests on GitHub Actions.

### Phase 1: MVP Functional Gateway (Week 2)
- OpenAI-compatible `POST /v1/chat/completions` endpoint (non-streaming & SSE streaming).
- Gateway API Key authentication with SHA-256 hashed persistence.
- Provider Adapter architecture with 2 live adapters (Google Gemini Direct, OpenRouter) and 2 mock adapters.
- Deterministic priority routing engine based on configured model aliases (e.g. `auto/coding` → [Primary: MockA, Secondary: MockB]).
- Database migrations with Alembic; seeding scripts for default routes and keys.

### Phase 2: Distributed Resilience & Rate Limiting (Week 3)
- Distributed Rate Limiter using Redis (sliding-window log / token bucket via atomic Lua scripts).
- Distributed In-flight Concurrency Limiter (lease/release mechanics per tenant key).
- Pre-stream retry engine with exponential backoff and jitter.
- Circuit Breaker per provider route (Closed, Open, Half-Open state machine).
- Graceful shutdown handling with connection draining.

### Phase 3: Observability & Operational Insights (Week 4)
- OpenTelemetry instrumentation (spans for Auth, RateLimit, RouteSelection, ProviderAttempt, StreamProxy).
- Prometheus metrics exporter (`crouter_requests_total`, `crouter_request_duration_seconds`, `crouter_circuit_breaker_state`).
- Redaction filters ensuring zero prompt/response/secret leakage in logs and traces.
- Pre-configured Grafana dashboard JSON definitions for instant visualization.

### Phase 4: Platform Showcase & Local Kubernetes (Post-MVP)
- Multi-replica deployment on local Kubernetes using `kind`.
- Readiness and liveness probes (`/health/ready`, `/health/live`).
- Automated k6 load benchmark scripts measuring gateway-added latency under 1,000 req/s.
- Failure postmortem documentation demonstrating automated recovery under chaos testing.
- Optional read-only Next.js administration dashboard.

---

## 6. Core Architectural Workflows

### 6.1 Standard Request Flow (Non-Streaming)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client / SDLCraft
    participant GW as CRouter Gateway
    participant Redis as Redis Cache/Limiter
    participant DB as PostgreSQL
    participant Adapter as Provider Adapter
    participant Upstream as AI Provider / Mock

    Client->>GW: POST /v1/chat/completions (Bearer gw_key)
    GW->>DB: Validate Key Hash & Fetch Tenant Policy
    GW->>Redis: Atomic Check & Increment (Rate Limit + In-flight Lease)
    alt Rate Limit Exceeded
        Redis-->>GW: Limit Exceeded (Remaining: 0)
        GW-->>Client: HTTP 429 (rate_limit_exceeded, Retry-After)
    else Limit Allowed
        Redis-->>GW: Quota Granted
        GW->>GW: Resolve Alias (e.g. "auto/coding" -> [RouteA, RouteB])
        GW->>Adapter: Dispatch to RouteA
        Adapter->>Upstream: HTTP Request (Provider API)
        Upstream-->>Adapter: HTTP 200 OK (Completion JSON)
        Adapter->>GW: Normalized Response Object
        GW->>Redis: Release In-flight Concurrency Lease
        GW->>DB: Log Request Event Metadata (Tokens, Duration, Route)
        GW-->>Client: HTTP 200 OK (OpenAI Compatible Envelope)
    end
```

### 6.2 Pre-Stream Failover & Circuit Breaker Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client Application
    participant GW as CRouter Gateway
    participant Breaker as Circuit Breaker
    participant RouteA as Primary Provider (Mock A)
    participant RouteB as Fallback Provider (Mock B)

    Client->>GW: POST /v1/chat/completions (model: "auto/coding")
    GW->>Breaker: Check Route A Health
    Breaker-->>GW: State: CLOSED (Healthy)
    GW->>RouteA: Attempt 1 -> POST Upstream
    RouteA-->>GW: HTTP 503 Service Unavailable
    GW->>Breaker: Record Route A Failure (Failure Count: +1)
    Note over GW,RouteA: Pre-stream failover safe: No bytes committed to downstream client!
    GW->>GW: Evaluate Fallback Policy (Attempts < MaxAttempts)
    GW->>Breaker: Check Route B Health
    Breaker-->>GW: State: CLOSED (Healthy)
    GW->>RouteB: Attempt 2 -> POST Upstream
    RouteB-->>GW: HTTP 200 OK (Success)
    GW-->>Client: HTTP 200 OK (Served via Route B, header X-CRouter-Attempts: 2)
```

### 6.3 SSE Streaming Interruption Guardrails

```mermaid
flowchart TD
    Start([Inference Request stream=true]) --> Auth[Auth & Rate Limit Verified]
    Auth --> Select[Route Selected]
    Select --> Connect[Connect to Upstream SSE Stream]
    Connect --> CheckByte{First Chunk Emitted to Client?}
    
    CheckByte -- No: Upstream Failed 5xx/Timeout --> Failover[Trigger Safe Fallback Route]
    Failover --> Connect
    
    CheckByte -- Yes: Stream Active --> StreamData[Proxy SSE Chunks chunk-by-chunk]
    StreamData --> Disconnect{Network Drops Mid-Stream?}
    
    Disconnect -- No --> Finish([Stream End [DONE]])
    Disconnect -- Yes --> Abort([Emit Abort Event / Terminate Connection])
    Abort --> Audit[Log 'interrupted' Event. Do NOT switch provider mid-stream!]
```

---

## 7. Functional Requirements

### FR-01: OpenAI API Compatibility [Priority: P0]
- Implement `POST /v1/chat/completions` adhering to OpenAI request/response specifications.
- **Supported Parameters (P0):** `model` (alias or explicit name), `messages` (`role`, `content`), `temperature`, `max_tokens`, `stream` (boolean).
- **Unsupported Parameter Handling:** Request containing unsupported parameters (e.g. `logprobs`, `modalities`) must return HTTP 400 with descriptive error detail rather than failing silently.
- **Model Discovery:** Implement `GET /v1/models` returning all active public aliases configured on the gateway.
- **Health Probes:** Implement lightweight `GET /health/live` (process alive) and `GET /health/ready` (database and Redis connections responsive).

### FR-02: Authentication & Key Management [Priority: P0]
- Clients authenticate via HTTP Header: `Authorization: Bearer cr_live_<random_token>`.
- **Zero Raw Key Storage:** The database stores only SHA-256 hashes (`key_hash`) and a truncated display prefix (e.g. `cr_live_a1b2...`).
- CLI-based administration:
  - `crouter keys create --tenant "sdcraft" --rate-limit 120 --concurrency 10`
  - `crouter keys revoke <key_prefix>`
  - `crouter keys list`
- Strict separation between gateway keys and upstream provider secrets. Upstream keys are never exposed over API.

### FR-03: Provider Adapter Interface [Priority: P0]
- Standardized abstract base class `BaseProviderAdapter`:
  - `validate_config()`: Validates API credentials and endpoint URLs.
  - `map_request(request: UnifiedChatRequest) -> UpstreamRequest`: Normalizes payload into provider format.
  - `send_completion(request: UpstreamRequest) -> UnifiedChatResponse`: Non-streaming execution.
  - `stream_completion(request: UpstreamRequest) -> AsyncIterator[UnifiedStreamChunk]`: SSE streaming execution.
  - `map_error(upstream_error: Exception) -> GatewayError`: Maps provider status codes to standard gateway error enums.
- **Adapter Registry:**
  1. `GeminiAdapter`: Direct integration with Google Gemini REST API (`v1beta`).
  2. `OpenRouterAdapter`: Integration with OpenRouter chat completions API.
  3. `MockAdapter`: Built-in local adapter supporting programmable latency, error codes, and token sequences.

### FR-04: Routing Engine & Aliasing [Priority: P0]
- Support virtual model aliases mapped to ordered priority lists:
  ```json
  {
    "alias": "auto/coding",
    "routes": [
      {"provider": "gemini", "model": "gemini-1.5-flash", "priority": 1, "timeout_ms": 5000},
      {"provider": "openrouter", "model": "meta-llama/llama-3-70b-instruct", "priority": 2, "timeout_ms": 7000},
      {"provider": "mock-b", "model": "mock-deterministic", "priority": 3, "timeout_ms": 2000}
    ]
  }
  ```
- **Execution Strategy:** Tries highest priority route. If route is unhealthy (circuit breaker open) or returns retryable error, moves sequentially down the fallback chain.
- Exclude routes exceeding configured cost ceilings or missing required tenant permissions.

### FR-05: Rate Limiting & Concurrency Leases [Priority: P1]
- **Shared Sliding-Window Rate Limiter:** Backed by Redis sorted sets (`ZSET`) or atomic token bucket via Lua scripts.
- **In-flight Concurrency Leaser:** Every active request increments key `concurrency:{key_id}` with an automatic TTL lease (default 60s). Decrements upon completion or cancellation.
- If Redis is unreachable, multi-tenant gateway fails closed to prevent unmetered overload.

### FR-06: Resilience: Circuit Breaker & Safe Retries [Priority: P1]
- **Circuit Breaker States:**
  - `CLOSED`: Normal operation; failure count tracked.
  - `OPEN`: Trips if error rate exceeds 50% over a 10-request sliding window. Fails fast without invoking upstream provider.
  - `HALF-OPEN`: After a cool-down window (default 30s), routes a single canary request to test upstream recovery.
- **Safe Pre-Stream Failover:** Retries are strictly forbidden once the first SSE byte or HTTP response header is sent to the client.

### FR-07: Telemetry, Observability & Scrubbing [Priority: P1]
- Distributed tracing using **OpenTelemetry (OTel)** with spans:
  - `crouter.auth` -> `crouter.ratelimit` -> `crouter.route_select` -> `crouter.upstream_attempt` -> `crouter.stream`.
- Prometheus metrics:
  - `crouter_http_requests_total{model, provider, status_code}`
  - `crouter_http_duration_seconds_bucket{model, provider, le}`
  - `crouter_active_in_flight_requests{tenant_id}`
  - `crouter_circuit_breaker_status{route_id, state}`
- **Data Privacy Scrubbing:** Loggers, metric labels, and trace tags MUST strip prompt text, generated tokens, and Authorization bearer headers.

### FR-08: Benchmarking & Chaos Testing Harness [Priority: P1]
- Standalone load test scripts (k6 and Locust) capable of running against local Docker Compose.
- Fault injection configurations for the Mock Provider:
  - Inject 503 on 30% of requests.
  - Inject 1500ms latency jitter.
  - Inject stream disconnection after 5 chunks.
- Measure and generate automated reports on gateway processing overhead (target: `< 5ms` p95 overhead).

---

## 8. Public API Contract & Error Model

### 8.1 Endpoint Specification

#### `POST /v1/chat/completions`

##### Request Headers
```http
Authorization: Bearer cr_live_8f3a9e...
Content-Type: application/json
X-Request-ID: req_01HV8Z7K... (Optional client trace ID)
```

##### Request Body
```json
{
  "model": "auto/coding",
  "messages": [
    {
      "role": "system",
      "content": "You are a senior platform engineer assisting with architecture."
    },
    {
      "role": "user",
      "content": "Design a resilient circuit breaker pattern."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

##### Success Response (`200 OK`)
```json
{
  "id": "chatcmpl_cr_01HV8Z8A3P...",
  "object": "chat.completion",
  "created": 1726906204,
  "model": "auto/coding",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "A resilient circuit breaker consists of three primary states: Closed, Open, and Half-Open..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 64,
    "total_tokens": 92
  }
}
```

##### Response Diagnostic Headers
```http
X-CRouter-Request-ID: req_01HV8Z8A3P...
X-CRouter-Provider-Selected: gemini
X-CRouter-Model-Selected: gemini-1.5-flash
X-CRouter-Attempts: 1
X-CRouter-Latency-Gateway-Ms: 3.4
X-CRouter-Latency-Upstream-Ms: 412.1
```

### 8.2 Standardized Error Envelope

When any error occurs, CRouter guarantees a unified JSON envelope compatible with standard OpenAI SDK error parsers:

```json
{
  "error": {
    "message": "Rate limit exceeded for API key. Quota resets in 14 seconds.",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded",
    "param": null,
    "request_id": "req_01HV8Z8A3P..."
  }
}
```

#### Error Code Mapping

| HTTP Code | Gateway Error Code | Trigger Condition |
|---|---|---|
| **400** | `invalid_request_error` | Missing required fields, invalid JSON, unsupported parameters. |
| **401** | `invalid_api_key` | Missing Bearer token or hash mismatch in database. |
| **403** | `forbidden_route` | Gateway key lacks permission to call the requested model alias. |
| **404** | `model_not_found` | Requested model alias or provider route does not exist. |
| **429** | `rate_limit_exceeded` | Sliding window rate limit or concurrent connection lease exceeded. |
| **502** | `upstream_provider_error` | Upstream provider returned an unparseable response or non-retryable 5xx. |
| **503** | `no_healthy_route` | All configured fallback routes are down or tripped by circuit breakers. |
| **504** | `gateway_timeout` | Total request deadline exceeded across all routing attempts. |

---

## 9. Technical Architecture & Component Design

### 9.1 High-Level Architecture Diagram

```
                              ┌───────────────────────────────────┐
                              │        Client Application         │
                              │   (Curl / OpenAI SDK / SDLCraft)  │
                              └─────────────────┬─────────────────┘
                                                │
                                     HTTP / SSE Requests
                                                │
                              ┌─────────────────▼─────────────────┐
                              │          CRouter Gateway          │
                              │       FastAPI Core Engine         │
                              └────────┬───────┬────────┬─────────┘
                                       │       │        │
                   ┌───────────────────┘       │        └────────────────────┐
                   ▼                           ▼                             ▼
         ┌───────────────────┐       ┌───────────────────┐         ┌───────────────────┐
         │    PostgreSQL     │       │   Redis 7.0+      │         │   OTel Collector  │
         │  Metadata Store   │       │ Rate/Concurrency  │         │   & Prometheus    │
         │ (Keys, Routes)    │       │ Circuit Breakers  │         │ (Traces, Metrics) │
         └───────────────────┘       └───────────────────┘         └───────────────────┘
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

### 9.2 Technology Stack Justification

| Component | Technology | Technical Rationale |
|---|---|---|
| **Language & Runtime** | Python 3.12 + AsyncIO | Native async ecosystem, excellent typed contracts, native to AI engineering. |
| **Web Framework** | FastAPI + Pydantic v2 | High throughput async ASGI, automatic OpenAPI generation, sub-millisecond serialization. |
| **HTTP Client Engine** | HTTPX (AsyncClient) | HTTP/2 support, connection pooling, native streaming, SSE event parsing. |
| **Relational Storage** | PostgreSQL 16 + SQLAlchemy 2.0 | Acid transactions for API key state, route priority definitions, and audit events. |
| **Database Migrations**| Alembic | Deterministic schema version control. |
| **Transient Shared State**| Redis 7 + `redis-py` async | Sub-millisecond distributed locks, atomic Lua scripting for rate limiting and circuit breakers. |
| **Telemetry & Metrics**| OpenTelemetry SDK + Prometheus | Vendor-neutral industry standard for traces and time-series metrics. |
| **Local Mock Engine** | FastAPI Mock Subservice | Deterministic simulation of latency, 429/503 faults, SSE streaming with zero external token cost. |
| **Container Runtime** | Docker Compose / kind K8s | Zero-cloud local orchestration reproducible on macOS, Linux, and Windows. |

---

## 10. Data Model & State Management

### 10.1 PostgreSQL Relational Schema

```mermaid
erDiagram
    TENANTS ||--o{ API_KEYS : owns
    TENANTS ||--o{ REQUEST_EVENTS : generates
    MODEL_ROUTES }o--|| PROVIDERS : references
    ROUTING_POLICIES ||--o{ MODEL_ROUTES : configures

    TENANTS {
        uuid id PK
        string name
        boolean is_active
        timestamp created_at
    }

    API_KEYS {
        uuid id PK
        uuid tenant_id FK
        string key_hash
        string key_prefix
        int rate_limit_rpm
        int max_concurrency
        timestamp revoked_at
        timestamp created_at
    }

    PROVIDERS {
        uuid id PK
        string name
        string provider_type
        string base_url
        string secret_env_var
        boolean is_active
    }

    ROUTING_POLICIES {
        uuid id PK
        string alias UK
        string description
        int max_retries
        int timeout_ms
    }

    MODEL_ROUTES {
        uuid id PK
        uuid policy_id FK
        uuid provider_id FK
        string upstream_model
        int priority
        int weight
        boolean is_enabled
    }

    REQUEST_EVENTS {
        uuid id PK
        uuid tenant_id FK
        string request_id
        string model_alias
        string selected_provider
        int status_code
        int duration_ms
        int prompt_tokens
        int completion_tokens
        decimal estimated_cost_usd
        timestamp created_at
    }
```

### 10.2 Redis Key Schema & TTL

| Redis Key Pattern | Data Structure | TTL | Purpose |
|---|---|---|---|
| `crouter:ratelimit:{key_id}:{minute_epoch}` | Counter / String | 120s | Fixed/sliding window rate counter per API key. |
| `crouter:concurrency:{key_id}` | Integer | 60s (sliding) | Current in-flight request count for the tenant key. |
| `crouter:breaker:{route_id}:state` | String (`CLOSED`/`OPEN`/`HALF`) | None | Dynamic circuit breaker state. |
| `crouter:breaker:{route_id}:failures` | Counter | 60s | Rolling failure counter for threshold tripping. |

---

## 11. Non-Functional Requirements (NFR)

### 11.1 Performance & Latency Targets
- **Gateway Added Latency (Overhead):** The gateway must add **$\le$ 5ms (p95)** and **$\le$ 15ms (p99)** latency overhead on non-streaming requests compared to direct mock calls.
- **Throughput:** A single gateway worker instance must handle **$\ge$ 500 requests/second** against local mock providers with `< 1%` CPU throttling on modern 4-core hardware.
- **Memory Footprint:** Baseline memory usage per worker process must remain below **150MB RSS**.

### 11.2 Reliability & Fault Tolerance
- **Graceful Shutdown:** On `SIGTERM`, stop accepting new connections and allow active requests up to 15 seconds to finish streaming.
- **Fail-Safe Circuit Breakers:** A failing upstream provider must never exhaust client timeout budgets; open breakers reject or reroute immediately within 1ms.
- **No Unbounded Retries:** Requests are bounded by strict attempt counts ($\le 3$) and end-to-end deadlines ($\le 15,000\text{ms}$).

### 11.3 Security, Privacy & Secret Protection
- **Zero Prompt Persistence:** Prompt texts, completions, and messages are never stored in PostgreSQL, logs, or traces.
- **Hashed Secrets:** Gateway keys are hashed with SHA-256 before insertion. Provider API keys are injected exclusively via environment variables (`.env`) or Docker secrets.
- **SSRF Prevention:** Upstream adapter URLs are strictly validated against allowlists; clients cannot supply arbitrary target endpoints.

---

## 12. Success Metrics & Evidence

To serve as a high-impact engineering portfolio, CRouter provides verifiable, reproducible evidence:

| Dimension | Proof / Artifact | Location in Repo |
|---|---|---|
| **API Contract Adherence** | 100% passing contract tests using official OpenAI Python SDK. | `tests/contract/test_openai_compatibility.py` |
| **Pre-Stream Failover** | Recorded integration test proving seamless recovery from 503 to mock fallback. | `tests/integration/test_failover.py` |
| **Distributed Concurrency** | Race-condition test with 2 gateway replicas enforcing shared quota in Redis. | `tests/integration/test_distributed_limits.py` |
| **Zero-Token Verification** | Full test suite execution showing 0 external HTTP requests outside localhost. | `tests/` (executed with `pytest --block-network`) |
| **Performance Benchmark** | k6 benchmark summary artifact showing p50/p95 gateway latency distribution. | `docs/benchmarks/load_test_report.md` |
| **Observability Artifact** | Grafana dashboard screenshot + scrubbed OpenTelemetry trace JSON. | `docs/assets/dashboard_trace.png` |

---

## 13. Comprehensive Failure & Test Matrix

| Test ID | Injected Scenario | Upstream Condition | Expected Gateway Behavior |
|---|---|---|---|
| **TC-01** | Happy Path Non-Streaming | Mock returns 200 OK after 50ms | HTTP 200 returned to client; metrics recorded; duration logged. |
| **TC-02** | Happy Path SSE Streaming | Mock emits 10 SSE chunks over 500ms | Client receives chunks in real-time; ends with `data: [DONE]`. |
| **TC-03** | Missing API Key | Client provides no `Authorization` header | Immediate HTTP 401 (`invalid_api_key`); no database lookup. |
| **TC-04** | Revoked API Key | Key hash exists in DB with `revoked_at` set | HTTP 401 (`invalid_api_key`); zero upstream calls. |
| **TC-05** | Unknown Model Alias | Client requests `"model": "unknown/v9"` | HTTP 404 (`model_not_found`); lists available models in detail. |
| **TC-06** | Primary Provider 503 | Primary route throws HTTP 503 | Gateway fails over to secondary route; client gets 200 OK. |
| **TC-07** | Primary Provider 429 | Primary route returns 429 quota exhausted | Route marked transiently throttled; fails over to secondary. |
| **TC-08** | Primary Provider Timeout | Primary route exceeds 3000ms deadline | Request aborted; retry budget checks secondary route. |
| **TC-09** | All Routes Unavailable | Both Primary and Fallback return 503 | HTTP 503 (`no_healthy_route`) returned with unified error body. |
| **TC-10** | Rate Limit Burst | Client exceeds 60 RPM limit | HTTP 429 (`rate_limit_exceeded`) with accurate `Retry-After`. |
| **TC-11** | Concurrency Ceiling | Client opens 20 simultaneous connections | Requests $\ge 11$ receive HTTP 429 concurrency limit error. |
| **TC-12** | Mid-Stream Disconnect | Mock drops connection after 4 chunks | Stream terminated with error; no cross-provider failover. |
| **TC-13** | Client Early Abort | Client cancels HTTP connection | Upstream socket canceled immediately; concurrency lease freed. |
| **TC-14** | Redis Outage | Redis server process terminated | Multi-tenant mode fails closed with 500 error; zero unmetered leaks. |

---

## 14. Repository & Directory Structure

```text
crouter/
├── apps/
│   ├── gateway/                     # Core FastAPI Application
│   │   ├── api/
│   │   │   ├── deps.py              # Auth, Redis, and DB dependencies
│   │   │   ├── v1/
│   │   │   │   ├── chat.py          # /v1/chat/completions endpoint
│   │   │   │   └── models.py        # /v1/models endpoint
│   │   │   └── health.py            # /health/live, /health/ready
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings (.env loader)
│   │   │   ├── errors.py            # Standardized exception definitions
│   │   │   └── telemetry.py         # OpenTelemetry & Prometheus setup
│   │   ├── engine/
│   │   │   ├── router.py            # Route resolution & priority fallback
│   │   │   ├── breaker.py           # Circuit breaker state engine
│   │   │   └── limiter.py           # Redis sliding-window & concurrency leases
│   │   ├── models/                  # SQLAlchemy ORM definitions
│   │   ├── schemas/                 # Pydantic request & response contracts
│   │   └── main.py                  # ASGI entry point
│   └── mock_provider/               # Deterministic Mock Subservice (Rp0)
│       └── main.py                  # Fault-injectable FastAPI mock server
├── packages/
│   └── adapters/                    # Provider Adapters
│       ├── base.py                  # Abstract Base Adapter
│       ├── gemini.py                # Google Gemini Direct Adapter
│       ├── openrouter.py            # OpenRouter Adapter
│       └── mock.py                  # Local Mock Adapter
├── migrations/                      # Alembic Database Migrations
│   ├── versions/
│   └── env.py
├── infra/
│   ├── compose/
│   │   ├── docker-compose.yml       # Complete local stack (Gateway, DB, Redis, Mock)
│   │   └── Dockerfile.gateway
│   ├── k8s/                         # Phase 4: Local Kubernetes manifests (kind)
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── observability/
│       ├── prometheus.yml
│       └── grafana-dashboard.json
├── tests/
│   ├── contract/                    # OpenAI SDK compatibility tests
│   ├── unit/                        # Unit tests for router, breaker, limiter
│   ├── integration/                 # Failover, rate limits, multi-replica tests
│   └── load/                        # k6 & Locust benchmark scripts
├── docs/
│   ├── architecture.md
│   ├── benchmarks.md
│   └── runbook.md
├── pyproject.toml                   # UV / Poetry dependencies
├── .env.example                     # Environment template (No real keys needed)
├── PRD.md                           # This Product Requirements Document
├── README.md                        # Project landing page & quickstart
└── LICENSE                          # Apache 2.0 / MIT
```

---

## 15. Implementation Roadmap & Ticket Breakdown

| Ticket | Scope | Deliverable | Acceptance Criteria |
|---|---|---|---|
| **CR-01** | Phase 0 | Project scaffolding, Docker Compose, Alembic setup | `docker compose up` starts Postgres, Redis, and Gateway without error. |
| **CR-02** | Phase 0 | Deterministic Mock Provider Service | Mock can return 200, 429, 503, custom delays, and SSE chunks via query params. |
| **CR-03** | Phase 1 | Database models & Gateway Key Auth CLI | `crouter keys create` writes hashed key; requests with valid Bearer pass auth. |
| **CR-04** | Phase 1 | OpenAI Schema Contracts & `/v1/chat/completions` | Pydantic v2 models match OpenAI API schema; rejects unsupported attributes. |
| **CR-05** | Phase 1 | Provider Adapter Base & Mock Adapter | Gateway routes requests to Mock Adapter; non-streaming and streaming work. |
| **CR-06** | Phase 1 | Live Gemini & OpenRouter Adapters | Direct REST adapters convert OpenAI schema to provider dialect correctly. |
| **CR-07** | Phase 1 | Alias Registry & Priority Route Selector | `"auto/coding"` resolves to ordered routes based on priority. |
| **CR-08** | Phase 2 | Redis Sliding-Window Rate Limiter | Exceeding RPM threshold returns 429 with `Retry-After`. |
| **CR-09** | Phase 2 | Distributed In-flight Concurrency Leaser | Concurrent requests capped at tenant limit; auto-releases on finish/abort. |
| **CR-10** | Phase 2 | Circuit Breaker & Pre-Stream Failover | Upstream 503 automatically falls over to secondary route without client error. |
| **CR-11** | Phase 3 | OpenTelemetry Traces & Prometheus Metrics | Requests generate spans; Prometheus exposes duration buckets and error counts. |
| **CR-12** | Phase 3 | PII & Secret Redaction Middleware | Logs and traces verified clean of prompt texts, tokens, and authorization keys. |
| **CR-13** | Phase 4 | k6 Load Test Suite & Benchmark Documentation | 1,000 req/s benchmark executed against mocks; report published to `docs/`. |
| **CR-14** | Phase 4 | Local Kubernetes `kind` Manifests | 2 gateway pods running on `kind` sharing Redis limits with rolling updates. |

---

## 16. Risk Management & Mitigations

| Risk | Impact | Likelihood | Mitigation Strategy |
|---|---|---|---|
| **Accidental API Charges** | High | Low | Gateway defaults strictly to local Mock Providers in `.env.example`. Real provider calls require explicit opt-in flags and API keys. |
| **High Gateway Overhead** | Medium | Medium | Use async I/O throughout, persistent HTTP connection pools, zero disk I/O in hot path, and Pydantic v2 C-extensions. |
| **Upstream Schema Changes** | Medium | High | Decouple internal representations using the adapter layer; validate schemas against provider contract tests in CI. |
| **Duplicate Billing on Timeout**| High | Medium | Enforce strict attempt budgets; do not retry ambiguous timeouts on non-idempotent endpoints without operator policy consent. |
| **Redis Outage Freezes Traffic**| High | Low | Document fail-closed behavior for multi-tenant production; provide explicit single-instance in-memory fallback for offline development. |

---

## 17. Zero-Budget Development & Cost Policy

### 17.1 The Rp0 Development Promise

CRouter is engineered so that **any developer can build, test, and demonstrate the entire platform for exactly Rp0**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Zero-Budget MVP Matrix                          │
├───────────────────────────────┬────────────────────────────────────────┤
│ Layer                         │ Cost / Method                          │
├───────────────────────────────┼────────────────────────────────────────┤
│ Application Engine            │ Python + FastAPI (Free / Open Source)  │
│ Database & Cache              │ Local Docker Postgres + Redis (Rp0)    │
│ Inference Testing             │ Local Deterministic Mock Engine (Rp0)  │
│ CI / Automated Testing        │ GitHub Actions Free Tier (Rp0)         │
│ Telemetry & Dashboards        │ Local OpenTelemetry + Prometheus (Rp0) │
│ Load Benchmarking             │ Local k6 / Locust (Rp0)                │
│ Container Orchestration       │ Local Docker Compose & kind (Rp0)      │
│ Real Model Smoke Testing      │ Optional: Gemini Free Tier / OpenRouter│
└───────────────────────────────┴────────────────────────────────────────┘
```

### 17.2 Rule of Engagement for Live Providers
1. Real provider credentials (Google AI Studio, OpenRouter) are strictly optional and disabled by default.
2. Live calls must only be executed during Phase 1 opt-in smoke tests.
3. Automated test suites (`pytest`, `k6`) must always execute against local mock adapters.

---

## 18. Architecture Decision Records (ADR) & Defaults

### ADR-01: Name and Project Identity
- **Decision:** The project is named **CRouter** (short for *Cloud Router* or *Central Router*).
- **Branding:** Tagline: *"One Gateway. Every Model."*
- **Identifiers:** GitHub: `arsyadal/crouter`, CLI: `crouter`, Docker: `crouter/gateway`.

### ADR-02: Synchronous Chat Path vs. Job Queues
- **Decision:** Do NOT place an asynchronous job queue (Celery, BullMQ) in the synchronous `POST /v1/chat/completions` request path.
- **Rationale:** LLM chat completions require immediate streaming response to downstream clients. Concurrency is governed via distributed semaphore leases in Redis, avoiding queue ingestion overhead.

### ADR-03: Response Caching
- **Decision:** Response caching is disabled by default in MVP.
- **Rationale:** LLM generation is inherently probabilistic and contains private user prompts. Premature caching risks stale completions and tenant cross-contamination.

### ADR-04: Failover Timing Boundary
- **Decision:** Failover is allowed **strictly before** the first chunk is sent to the client.
- **Rationale:** Switching models mid-stream produces garbled, incoherent text completions and breaks client JSON/SSE parsers.

---

## 19. First-Run Acceptance Demo Script

When onboarding an evaluator, recruiter, or new contributor, the following command sequence validates the operational readiness of CRouter with **zero credentials required**:

```bash
# 1. Clone repository
git clone https://github.com/arsyadal/crouter.git
cd crouter

# 2. Setup environment (defaults to 100% local mock mode)
cp .env.example .env

# 3. Boot local infrastructure (Gateway, Postgres, Redis, Mock Provider)
docker compose -f infra/compose/docker-compose.yml up --build -d

# 4. Provision initial gateway API key for local tenant
docker compose -f infra/compose/docker-compose.yml exec gateway \
    crouter keys create --tenant "demo-agent" --rate-limit 60 --concurrency 5
# Output: Generated Key: cr_live_demo1234567890abcdef (Raw key shown once)

# 5. Execute standard completion request via mock provider (Rp0)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer cr_live_demo1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto/coding",
    "messages": [{"role": "user", "content": "Hello CRouter!"}],
    "stream": false
  }'

# 6. Simulate Upstream Provider A Failure (Inject 503) & Verify Automated Failover
curl -X POST http://localhost:8001/mock/inject-fault?status=503&target=mock-a
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer cr_live_demo1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto/coding",
    "messages": [{"role": "user", "content": "Test failover resilience"}],
    "stream": false
  }'
# Notice header: X-CRouter-Provider-Selected: mock-b (Automated failover succeeded!)

# 7. Run complete zero-token test suite
docker compose -f infra/compose/docker-compose.yml exec gateway pytest
```

---

*Document finalized and ready for development.*
