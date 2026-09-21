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
    ):
        self.circuit_breaker = circuit_breaker
        self.adapter_overrides = adapter_overrides or {}

    def get_adapter(self, candidate: RouteCandidate) -> BaseProviderAdapter:
        if candidate.provider_name in self.adapter_overrides:
            return self.adapter_overrides[candidate.provider_name]

        # Resolve api key from env if secret_env_var is set
        import os

        api_key = None
        if candidate.secret_env_var:
            api_key = os.environ.get(candidate.secret_env_var)

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
                    enabled_routes = [r for r in policy.routes if r.is_enabled and r.provider.is_active]
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

        raise ModelNotFoundError(
            f"Requested model or alias '{model_alias}' not found in gateway registry."
        )

    async def execute_non_streaming(
        self,
        request: ChatCompletionRequest,
        db: Optional[AsyncSession] = None,
    ) -> Tuple[ChatCompletionResponse, RouteCandidate, int, float]:
        """Execute non-streaming request with pre-stream priority failover.

        Returns: (response, selected_route, attempts, upstream_latency_ms)
        """
        candidates = await self.resolve_routes(request.model, db)
        attempts = 0
        last_error: Optional[Exception] = None

        for candidate in candidates:
            route_key = candidate.route_key
            if not await self.circuit_breaker.can_execute(route_key):
                logger.warning(f"Skipping route {route_key}: circuit breaker is OPEN")
                continue

            attempts += 1
            adapter = self.get_adapter(candidate)
            start_time = time.perf_counter()

            try:
                response = await adapter.send_completion(
                    request, target_model=candidate.upstream_model
                )
                upstream_latency_ms = (time.perf_counter() - start_time) * 1000.0
                await self.circuit_breaker.record_success(route_key)
                return response, candidate, attempts, upstream_latency_ms

            except Exception as e:
                upstream_latency_ms = (time.perf_counter() - start_time) * 1000.0
                await self.circuit_breaker.record_failure(route_key)
                last_error = e
                logger.warning(
                    f"Route attempt {attempts} on {candidate.provider_name} failed: {e}"
                )
                # Continue loop to try next route candidate in chain

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
        """Execute streaming request with pre-stream priority failover.

        Pre-stream failover is allowed before the first chunk is emitted.
        Returns: (chunk_iterator, selected_route, attempts)
        """
        candidates = await self.resolve_routes(request.model, db)
        attempts = 0
        last_error: Optional[Exception] = None

        for candidate in candidates:
            route_key = candidate.route_key
            if not await self.circuit_breaker.can_execute(route_key):
                continue

            attempts += 1
            adapter = self.get_adapter(candidate)
            stream_gen = adapter.stream_completion(
                request, target_model=candidate.upstream_model
            )

            # Test receiving the first chunk before committing downstream
            try:
                first_chunk = await stream_gen.__anext__()
                await self.circuit_breaker.record_success(route_key)

                async def full_stream():
                    yield first_chunk
                    try:
                        async for chunk in stream_gen:
                            yield chunk
                    except Exception as stream_err:
                        logger.error(
                            f"Mid-stream connection error from {candidate.provider_name}: {stream_err}"
                        )
                        raise stream_err

                return full_stream(), candidate, attempts

            except StopAsyncIteration:
                # Stream ended immediately without chunks
                await self.circuit_breaker.record_success(route_key)

                async def empty_stream():
                    return
                    yield

                return empty_stream(), candidate, attempts

            except Exception as e:
                # Pre-stream failure! We haven't emitted bytes to client yet, so failover is safe!
                await self.circuit_breaker.record_failure(route_key)
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
