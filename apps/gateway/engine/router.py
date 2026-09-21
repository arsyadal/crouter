import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.gateway.core.errors import (
    CRouterException,
    ModelNotFoundError,
    NoHealthyRouteError,
    UpstreamProviderError,
    RateLimitExceededError,
    GatewayTimeoutError,
)
from apps.gateway.engine.breaker import CircuitBreaker
from apps.gateway.models.entities import RoutingPolicy, ModelRoute, Provider
from apps.gateway.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
)
from packages.adapters.base import BaseProviderAdapter
from packages.adapters.mock import MockAdapter
from packages.adapters.gemini import GeminiAdapter
from packages.adapters.openrouter import OpenRouterAdapter
from packages.adapters.commandcode import CommandCodeAdapter
from apps.gateway.engine.key_pool import ProviderKeyPool, key_pool as default_key_pool
from apps.gateway.core.config import settings

logger = logging.getLogger("crouter.router")


class RouteCandidate:
    def __init__(
        self,
        provider_name: str,
        provider_type: str,
        upstream_model: str,
        priority: int,
        base_url: Optional[str] = None,
        secret_env_var: Optional[str] = None,
        timeout_ms: int = 5000,
    ):
        self.provider_name = provider_name
        self.provider_type = provider_type
        self.upstream_model = upstream_model
        self.priority = priority
        self.base_url = base_url
        self.secret_env_var = secret_env_var
        self.timeout_ms = timeout_ms

    @property
    def route_key(self) -> str:
        return f"{self.provider_name}:{self.upstream_model}"


class RoutingEngine:
    def __init__(
        self,
        circuit_breaker: CircuitBreaker,
        adapter_overrides: Optional[Dict[str, BaseProviderAdapter]] = None,
        key_pool: Optional[ProviderKeyPool] = None,
    ):
        self.circuit_breaker = circuit_breaker
        self.adapter_overrides = adapter_overrides or {}
        self.key_pool = key_pool or default_key_pool
        # Populate key pool from configured settings if available
        if settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY:
            self.key_pool.load_from_env_or_string("gemini", settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY)
        if settings.OPENROUTER_API_KEYS or settings.OPENROUTER_API_KEY:
            self.key_pool.load_from_env_or_string("openrouter", settings.OPENROUTER_API_KEYS or settings.OPENROUTER_API_KEY)
        if settings.COMMANDCODE_API_KEYS or settings.COMMANDCODE_API_KEY:
            self.key_pool.load_from_env_or_string("commandcode", settings.COMMANDCODE_API_KEYS or settings.COMMANDCODE_API_KEY)
            self.key_pool.load_from_env_or_string("9router", settings.COMMANDCODE_API_KEYS or settings.COMMANDCODE_API_KEY)

        self._route_latency_ema: Dict[str, float] = {}
        self._alpha: float = 0.3

    def record_latency(self, route_key: str, latency_ms: float) -> None:
        """Record latency sample using exponential moving average (EMA)."""
        current = self._route_latency_ema.get(route_key)
        if current is None:
            self._route_latency_ema[route_key] = latency_ms
        else:
            self._route_latency_ema[route_key] = (
                self._alpha * latency_ms + (1.0 - self._alpha) * current
            )

    def get_latency(self, route_key: str) -> float:
        """Get tracked EMA latency in ms (defaults to 50.0ms)."""
        return self._route_latency_ema.get(route_key, 50.0)

    def get_adapter(self, candidate: RouteCandidate, api_key_override: Optional[str] = None) -> BaseProviderAdapter:
        if candidate.provider_name in self.adapter_overrides:
            return self.adapter_overrides[candidate.provider_name]

        # Resolve api key from override, key pool, or secret env var
        import os

        api_key = api_key_override
        if not api_key:
            if candidate.secret_env_var:
                raw_val = os.environ.get(candidate.secret_env_var)
                if raw_val:
                    self.key_pool.load_from_env_or_string(candidate.provider_name, raw_val)
                    self.key_pool.load_from_env_or_string(candidate.provider_type, raw_val)

            api_key = (
                self.key_pool.get_key(candidate.provider_name)
                or self.key_pool.get_key(candidate.provider_type)
            )

        ptype = candidate.provider_type.lower()
        timeout_s = max(1.0, candidate.timeout_ms / 1000.0)

        if ptype == "gemini":
            return GeminiAdapter(
                provider_name=candidate.provider_name,
                base_url=candidate.base_url,
                api_key=api_key or settings.GEMINI_API_KEY,
                timeout_seconds=timeout_s,
            )
        elif ptype == "openrouter":
            return OpenRouterAdapter(
                provider_name=candidate.provider_name,
                base_url=candidate.base_url,
                api_key=api_key or settings.OPENROUTER_API_KEY,
                timeout_seconds=timeout_s,
            )
        elif ptype in ("commandcode", "9router"):
            return CommandCodeAdapter(
                provider_name=candidate.provider_name,
                base_url=candidate.base_url or settings.COMMANDCODE_BASE_URL,
                api_key=api_key or settings.COMMANDCODE_API_KEY,
                timeout_seconds=timeout_s,
            )
        else:
            # Default to MockAdapter
            base = candidate.base_url or settings.MOCK_PROVIDER_URL
            return MockAdapter(
                provider_name=candidate.provider_name,
                base_url=base,
                timeout_seconds=timeout_s,
            )

    async def resolve_routes(
        self, model_alias: str, db: Optional[AsyncSession] = None
    ) -> List[RouteCandidate]:
        """Resolve ordered route candidates from DB or default mock configuration."""
        if db is not None:
            try:
                stmt = (
                    select(RoutingPolicy)
                    .where(RoutingPolicy.alias == model_alias)
                    .options(
                        selectinload(RoutingPolicy.routes).selectinload(
                            ModelRoute.provider
                        )
                    )
                )
                result = await db.execute(stmt)
                policy = result.scalars().first()

                if policy and policy.routes:
                    candidates = []
                    enabled_routes = [r for r in policy.routes if r.is_enabled and r.provider and r.provider.is_active]
                    enabled_routes.sort(key=lambda r: r.priority)
                    for r in enabled_routes:
                        candidates.append(
                            RouteCandidate(
                                provider_name=r.provider.name,
                                provider_type=r.provider.provider_type,
                                upstream_model=r.upstream_model,
                                priority=r.priority,
                                base_url=r.provider.base_url,
                                secret_env_var=r.provider.secret_env_var,
                                timeout_ms=policy.timeout_ms,
                            )
                        )
                    if candidates:
                        return candidates
            except Exception as e:
                logger.warning(f"Database route resolution error: {e}")

        # Built-in default policies
        if model_alias in ("auto/coding", "mock-default", "default"):
            return [
                RouteCandidate(
                    provider_name="mock-a",
                    provider_type="mock",
                    upstream_model="mock-deterministic",
                    priority=1,
                    base_url=settings.MOCK_PROVIDER_URL,
                    timeout_ms=5000,
                ),
                RouteCandidate(
                    provider_name="mock-b",
                    provider_type="mock",
                    upstream_model="mock-deterministic",
                    priority=2,
                    base_url=settings.MOCK_PROVIDER_URL,
                    timeout_ms=5000,
                ),
            ]

        # Built-in fast/chat policy
        if model_alias == "fast/chat":
            chat_candidates = []
            p_idx = 1
            if settings.COMMANDCODE_API_KEY:
                chat_candidates.append(
                    RouteCandidate(
                        provider_name="commandcode",
                        provider_type="commandcode",
                        upstream_model="inclusionai/ling-3.0-flash-sante:free",
                        priority=p_idx,
                        base_url=settings.COMMANDCODE_BASE_URL,
                        secret_env_var="COMMANDCODE_API_KEY",
                        timeout_ms=15000,
                    )
                )
                p_idx += 1
            chat_candidates.append(
                RouteCandidate(
                    provider_name="gemini",
                    provider_type="gemini",
                    upstream_model="gemini-1.5-flash",
                    priority=p_idx,
                    secret_env_var="GEMINI_API_KEY",
                    timeout_ms=10000,
                )
            )
            p_idx += 1
            chat_candidates.append(
                RouteCandidate(
                    provider_name="openrouter",
                    provider_type="openrouter",
                    upstream_model="meta-llama/llama-3.2-3b-instruct:free",
                    priority=p_idx,
                    secret_env_var="OPENROUTER_API_KEY",
                    timeout_ms=10000,
                )
            )
            return chat_candidates

        # Explicit provider format check: e.g. "mock-a" or "mock-b"
        if model_alias.startswith("mock-"):
            return [
                RouteCandidate(
                    provider_name=model_alias,
                    provider_type="mock",
                    upstream_model="mock-deterministic",
                    priority=1,
                    base_url=settings.MOCK_PROVIDER_URL,
                    timeout_ms=5000,
                )
            ]

        # Explicit direct Gemini model: e.g. "gemini-1.5-flash"
        if model_alias.startswith("gemini"):
            return [
                RouteCandidate(
                    provider_name="gemini",
                    provider_type="gemini",
                    upstream_model=model_alias,
                    priority=1,
                    secret_env_var="GEMINI_API_KEY",
                    timeout_ms=15000,
                )
            ]

        # Explicit direct OpenRouter model with openrouter/ prefix
        if model_alias.startswith("openrouter/"):
            target = model_alias.replace("openrouter/", "", 1)
            return [
                RouteCandidate(
                    provider_name="openrouter",
                    provider_type="openrouter",
                    upstream_model=target,
                    priority=1,
                    secret_env_var="OPENROUTER_API_KEY",
                    timeout_ms=15000,
                )
            ]

        # Alias: 9router or commandcode (auto-routes to free models)
        if model_alias in ("9router", "commandcode", "9router/chat"):
            return [
                RouteCandidate(
                    provider_name="commandcode",
                    provider_type="commandcode",
                    upstream_model="inclusionai/ling-3.0-flash-sante:free",
                    priority=1,
                    base_url=settings.COMMANDCODE_BASE_URL,
                    secret_env_var="COMMANDCODE_API_KEY",
                    timeout_ms=20000,
                ),
                RouteCandidate(
                    provider_name="commandcode",
                    provider_type="commandcode",
                    upstream_model="poolside/laguna-s-2.1-free",
                    priority=2,
                    base_url=settings.COMMANDCODE_BASE_URL,
                    secret_env_var="COMMANDCODE_API_KEY",
                    timeout_ms=20000,
                ),
            ]

        # Explicit direct 9Router / Command Code model with 9router/ or commandcode/ prefix
        if model_alias.startswith("9router/") or model_alias.startswith("commandcode/"):
            prefix = "9router/" if model_alias.startswith("9router/") else "commandcode/"
            target = model_alias.replace(prefix, "", 1)
            return [
                RouteCandidate(
                    provider_name="commandcode",
                    provider_type="commandcode",
                    upstream_model=target,
                    priority=1,
                    base_url=settings.COMMANDCODE_BASE_URL,
                    secret_env_var="COMMANDCODE_API_KEY",
                    timeout_ms=25000,
                )
            ]

        # Anthropic Claude models (e.g. claude-3-5-sonnet-20241022, claude-3-haiku, etc.)
        if model_alias.startswith("claude") or model_alias.startswith("anthropic/"):
            claude_candidates = []
            p_idx = 1
            if settings.COMMANDCODE_API_KEY or settings.COMMANDCODE_API_KEYS:
                claude_candidates.append(
                    RouteCandidate(
                        provider_name="commandcode",
                        provider_type="commandcode",
                        upstream_model="inclusionai/ling-3.0-flash-sante:free",
                        priority=p_idx,
                        base_url=settings.COMMANDCODE_BASE_URL,
                        secret_env_var="COMMANDCODE_API_KEY",
                        timeout_ms=25000,
                    )
                )
                p_idx += 1
            if settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEYS:
                claude_candidates.append(
                    RouteCandidate(
                        provider_name="openrouter",
                        provider_type="openrouter",
                        upstream_model="meta-llama/llama-3.2-3b-instruct:free",
                        priority=p_idx,
                        secret_env_var="OPENROUTER_API_KEY",
                        timeout_ms=20000,
                    )
                )
                p_idx += 1
            claude_candidates.append(
                RouteCandidate(
                    provider_name="mock-a",
                    provider_type="mock",
                    upstream_model="mock-deterministic",
                    priority=p_idx,
                    base_url=settings.MOCK_PROVIDER_URL,
                    timeout_ms=5000,
                )
            )
            return claude_candidates

        raise ModelNotFoundError(
            f"Requested model or alias '{model_alias}' not found in gateway registry."
        )

    async def execute_non_streaming(
        self,
        request: ChatCompletionRequest,
        db: Optional[AsyncSession] = None,
    ) -> Tuple[ChatCompletionResponse, RouteCandidate, int, float]:
        """Execute non-streaming request with pre-stream priority failover and latency ranking.

        Returns: (response, selected_route, attempts, upstream_latency_ms)
        """
        candidates = await self.resolve_routes(request.model, db)
        # Order candidates by priority first, then lowest tracked EMA latency
        candidates.sort(key=lambda c: (c.priority, self.get_latency(c.route_key)))
        attempts = 0
        last_error: Optional[Exception] = None

        for candidate in candidates:
            route_key = candidate.route_key
            if not await self.circuit_breaker.can_execute(route_key):
                logger.warning(f"Skipping route {route_key}: circuit breaker is OPEN")
                continue

            attempts += 1
            adapter = self.get_adapter(candidate)

            # Retry transient errors with exponential backoff and key rotation for live network providers
            max_retries = 2 if candidate.provider_type != "mock" else 0
            backoff_s = 0.05

            for retry_idx in range(max_retries + 1):
                adapter = self.get_adapter(candidate)
                start_time = time.perf_counter()
                try:
                    response = await adapter.send_completion(
                        request, target_model=candidate.upstream_model
                    )
                    upstream_latency_ms = (time.perf_counter() - start_time) * 1000.0
                    self.record_latency(route_key, upstream_latency_ms)
                    await self.circuit_breaker.record_success(route_key)
                    if getattr(adapter, "api_key", None):
                        self.key_pool.record_success(candidate.provider_name, adapter.api_key)
                    return response, candidate, attempts, upstream_latency_ms

                except (RateLimitExceededError, UpstreamProviderError) as e:
                    upstream_latency_ms = (time.perf_counter() - start_time) * 1000.0
                    err_str = str(e).lower()
                    is_rate_limit = any(t in err_str for t in ("429", "rate limit"))
                    if getattr(adapter, "api_key", None):
                        self.key_pool.record_error(
                            candidate.provider_name, adapter.api_key, is_rate_limit=is_rate_limit
                        )
                    if retry_idx < max_retries and (is_rate_limit or any(t in err_str for t in ("503", "504", "timeout"))):
                        logger.warning(
                            f"Transient error on {route_key}: {e}. Retrying with next key/attempt in {backoff_s:.3f}s (retry {retry_idx+1}/{max_retries})..."
                        )
                        await asyncio.sleep(backoff_s)
                        backoff_s *= 2.0
                        continue
                    await self.circuit_breaker.record_failure(route_key)
                    last_error = e
                    logger.warning(
                        f"Route attempt {attempts} on {candidate.provider_name} failed: {e}"
                    )
                    break

                except Exception as e:
                    upstream_latency_ms = (time.perf_counter() - start_time) * 1000.0
                    await self.circuit_breaker.record_failure(route_key)
                    if getattr(adapter, "api_key", None):
                        self.key_pool.record_error(candidate.provider_name, adapter.api_key)
                    last_error = e
                    logger.warning(
                        f"Route attempt {attempts} on {candidate.provider_name} failed: {e}"
                    )
                    break

        if last_error:
            raise NoHealthyRouteError(
                f"All configured fallback routes failed. Last error: {last_error}"
            )

        raise NoHealthyRouteError(
            "All configured fallback routes are unavailable or tripped by circuit breakers."
        )

    async def execute_streaming(
        self,
        request: ChatCompletionRequest,
        db: Optional[AsyncSession] = None,
    ) -> Tuple[AsyncIterator[ChatCompletionChunk], RouteCandidate, int]:
        """Execute streaming request with pre-stream priority failover and latency ranking.

        Pre-stream failover is allowed before the first chunk is emitted.
        Returns: (chunk_iterator, selected_route, attempts)
        """
        candidates = await self.resolve_routes(request.model, db)
        candidates.sort(key=lambda c: (c.priority, self.get_latency(c.route_key)))
        attempts = 0
        last_error: Optional[Exception] = None

        for candidate in candidates:
            route_key = candidate.route_key
            if not await self.circuit_breaker.can_execute(route_key):
                continue

            attempts += 1
            adapter = self.get_adapter(candidate)
            start_time = time.perf_counter()
            stream_gen = adapter.stream_completion(
                request, target_model=candidate.upstream_model
            )

            # Test receiving the first chunk before committing downstream
            try:
                first_chunk = await stream_gen.__anext__()
                first_chunk_latency_ms = (time.perf_counter() - start_time) * 1000.0
                self.record_latency(route_key, first_chunk_latency_ms)
                await self.circuit_breaker.record_success(route_key)
                if getattr(adapter, "api_key", None):
                    self.key_pool.record_success(candidate.provider_name, adapter.api_key)

                async def full_stream():
                    try:
                        yield first_chunk
                        async for chunk in stream_gen:
                            yield chunk
                    except Exception as stream_err:
                        logger.error(
                            f"Mid-stream connection error from {candidate.provider_name}: {stream_err}"
                        )
                        raise stream_err
                    finally:
                        if hasattr(stream_gen, "aclose"):
                            try:
                                await stream_gen.aclose()
                            except Exception:
                                pass

                return full_stream(), candidate, attempts

            except StopAsyncIteration:
                # Stream ended immediately without chunks
                await self.circuit_breaker.record_success(route_key)
                if getattr(adapter, "api_key", None):
                    self.key_pool.record_success(candidate.provider_name, adapter.api_key)

                async def empty_stream():
                    return
                    yield

                return empty_stream(), candidate, attempts

            except Exception as e:
                # Pre-stream failure! We haven't emitted bytes to client yet, so failover is safe!
                await self.circuit_breaker.record_failure(route_key)
                if getattr(adapter, "api_key", None):
                    err_str = str(e).lower()
                    is_rate_limit = any(t in err_str for t in ("429", "rate limit"))
                    self.key_pool.record_error(
                        candidate.provider_name, adapter.api_key, is_rate_limit=is_rate_limit
                    )
                last_error = e
                logger.warning(
                    f"Pre-stream attempt {attempts} on {candidate.provider_name} failed: {e}. Falling over..."
                )
                continue

        if last_error:
            raise NoHealthyRouteError(
                f"All fallback routes failed during stream initialization. Last error: {last_error}"
            )

        raise NoHealthyRouteError("All streaming routes are unavailable or tripped.")
