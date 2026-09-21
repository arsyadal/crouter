# CRouter: Technical Evaluation & Next-Step Implementation Roadmap

> **Document Status**: Active Implementation Guide (Post-PRD.md)  
> **Date**: 2026-09-21  
> **Target Goal**: Portfolio Centerpiece & Production Infrastructure Engineering

---

## 1. Architectural Justification: LiteLLM, 9Router, or Custom Gateway?

### The Question
> *"Kalau sudah ada 9Router dan LiteLLM, apakah masih perlu bikin gateway sendiri?"*

### Comparative Matrix

| Dimension | LiteLLM | 9Router | **CRouter (Custom Gateway)** |
|---|---|---|---|
| **Core Architecture** | Python monolith proxy / SDK wrapper | Managed upstream multi-provider API | Self-hosted micro-gateway with modular engine separation |
| **Failover Control** | Static config fallback list | Black-box upstream routing | Dynamic latency EMA ranking, half-open canary probes, pre-stream verification |
| **Distributed Rate Limiting** | Basic in-memory or Redis key-value | Upstream rate limits | Atomic Redis Lua sliding window (60s exact) + concurrency leasing |
| **Local Testing (Modal Rp0)** | Relies on third-party live keys | Paid/Free upstream tokens | Integrated programmable mock provider with fault injection |
| **Observability** | External plugins | Provider dashboard | Native OpenTelemetry W3C distributed tracing + Prometheus histograms |
| **Primary Value** | Rapid SDK integration | Model aggregation | **Platform engineering mastery & infrastructure portfolio** |

### Strategic Recommendation
- **For Fast Application Prototyping**: Use 9Router or LiteLLM.
- **For Backend & Infrastructure Engineering Portfolio**: Build and maintain CRouter. CRouter proves mastery of:
  1. Low-latency async Python (`FastAPI`, `asyncio`, `httpx`).
  2. Distributed synchronization primitives in Redis (atomic Lua scripts, concurrency locks).
  3. Resilient state machines (Circuit Breaker: CLOSED, OPEN, HALF-OPEN).
  4. Observability and distributed context propagation (OpenTelemetry W3C, Prometheus metrics).
  5. Cloud-native Kubernetes deployment and Horizontal Pod Autoscaling (HPA).

---

## 2. Completed Capabilities (Verified in Codebase)

The following capabilities are fully implemented and verified with automated test suites (`pytest` 100% passing):

### 1. Multi-Provider Intelligent Routing & Health Ranking
- **Engine**: `apps/gateway/engine/router.py`.
- **Dynamic Latency Ranking**: Tracks Exponential Moving Average (EMA) latency per provider route (`record_latency` with $\alpha = 0.3$).
- **Health-Aware Route Filtering**: Automatically skips routes whose circuit breaker is in `OPEN` state.
- **Pre-Stream Failover**: For SSE streams, tests the first token chunk before downstream commitment; on failure, fails over without broken pipes.
- **Real Upstream Default**: Routes `auto/coding` and `fast/chat` to real CommandCode/9Router models (e.g. `deepseek/deepseek-v4-flash`, `inclusionai/ling-3.0-flash-sante:free`).

### 2. Circuit Breaker & Exponential Backoff Retry
- **Engine**: `apps/gateway/engine/breaker.py`.
- **Three States**: `CLOSED` (normal), `OPEN` (tripped after threshold failures), `HALF_OPEN` (canary test).
- **Transient Retry with Exponential Backoff**: Retries transient 429/503/timeouts on upstream providers with backoff ($0.05\text{s} \times 2^n$) before tripping the circuit.
- **State Persistence**: Supports Redis cluster state synchronization with instant in-memory fallback.

### 3. Distributed Sliding-Window Rate Limiting & Concurrency Leasing
- **Engine**: `apps/gateway/engine/limiter.py`.
- **Sliding-Window Lua Script**: Atomic `ZREMRANGEBYSCORE`, `ZCARD`, `ZADD`, `EXPIRE` over a 60-second window.
- **Concurrency Leaser**: Atomic Redis `INCR` / `DECR` enforcing max in-flight requests per tenant.

### 4. Distributed Tracing (OpenTelemetry W3C) & Prometheus Metrics
- **Engine**: `apps/gateway/core/tracing.py`, `apps/gateway/core/telemetry.py`.
- **W3C TraceContext**: Parses and injects `traceparent` headers (`00-{trace_id}-{span_id}-01`) and exposes `X-Trace-ID`.
- **Prometheus Metrics**: Exposes `/metrics` endpoint with request counters, latency histograms, and circuit breaker gauges.
- **Zero-Leak Data Scrubbing**: Redacts `Authorization` tokens, API keys, and prompt payload PII from trace logs.

### 5. Kubernetes Scaling & Deployment
- **Manifests**: `infra/k8s/deployment.yaml`, `service.yaml`, `hpa.yaml`, `configmap.yaml`, `secret.yaml.example`, `ingress.yaml`.
- **Horizontal Pod Autoscaling**: Scaled from 2 to 10 replicas based on 70% CPU and 80% Memory utilization thresholds.

### 6. Benchmark Suite
- **Script**: `scripts/benchmark_latency.py` measures p50, p90, p95, p99, throughput (RPS), and provider distribution.

---

## 3. Next Step Implementation Roadmap (Phases 2 – 6)

### Phase 2: Semantic Caching with Redis Vector Similarity
- **Objective**: Eliminate redundant LLM calls and reduce upstream cost by caching identical or semantically similar prompts.
- **Implementation**:
  1. Add an embedding stage using a lightweight local embedding model or fast embedding API.
  2. Store embeddings in Redis using RedisVL or RediSearch vector indexes (`HSET` + `FT.SEARCH`).
  3. Query cache with cosine distance threshold $\ge 0.95$. On match, return cached response with header `X-CRouter-Cache: HIT`.

### Phase 3: Dynamic Budget Governance & Token Cost Accounting
- **Objective**: Prevent tenant cost overruns with hard financial limits.
- **Implementation**:
  1. Add `spend_limit_usd` and `current_spend_usd` fields to `Tenant` and `APIKey` entities.
  2. Track upstream token usage (`prompt_tokens`, `completion_tokens`) from response headers or body.
  3. Automatically calculate cost based on model pricing matrix (e.g. DeepSeek, Gemini, OpenRouter).
  4. If budget threshold reaches 90%, emit warning event; at 100%, reject with HTTP 402 / 429 or fall back to free models.

### Phase 4: Production PostgreSQL Migration & Read Replicas
- **Objective**: Transition from local SQLite to high-concurrency PostgreSQL.
- **Implementation**:
  1. Run Alembic migrations against PostgreSQL: `alembic upgrade head`.
  2. Configure connection pooling with asyncpg (`min_size=5`, `max_size=20`).
  3. Configure read replica routing for read-heavy admin dashboard queries (`/admin/overview`, `/admin/routes`).

### Phase 5: Production Observability (Grafana Dashboard & OTLP Collector)
- **Objective**: Enterprise-grade monitoring and alerting.
- **Implementation**:
  1. Deploy OpenTelemetry Collector (`otel-collector`) in Kubernetes.
  2. Export CRouter traces via gRPC/HTTP to Jaeger or Tempo.
  3. Import `infra/observability/grafana-dashboard.json` into Grafana.
  4. Configure Prometheus AlertManager rules for breaker trip events and p99 latency spikes ($> 2000\text{ms}$).

### Phase 6: Interactive Admin Dashboard Enhancements
- **Objective**: Polish Next.js dashboard for real-time visibility.
- **Implementation**:
  1. Add real-time trace inspection tab consuming `/admin/traces`.
  2. Add live provider latency chart using Prometheus metrics query.
  3. Add one-click manual route test tool in the playground.

---

## 4. Verification Evidence & Quick-Start Commands

### Run Full Test Suite
```bash
python -m pytest
```

### Run Live Upstream Tests (CommandCode)
```bash
python -m pytest tests/integration/test_live_traffic.py
```

### Run Latency Benchmark
```bash
python scripts/benchmark_latency.py --url http://localhost:8000 --model auto/coding -c 20 -n 100
```

### Apply Kubernetes Manifests
```bash
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml
kubectl apply -f infra/k8s/hpa.yaml
kubectl apply -f infra/k8s/ingress.yaml
```
