import hashlib
from typing import AsyncGenerator, Optional
from fastapi import Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload

from apps.gateway.core.config import settings
from apps.gateway.core.errors import InvalidAPIKeyError, RateLimitExceededError
from apps.gateway.engine.breaker import CircuitBreaker
from apps.gateway.engine.limiter import RateLimiter, ConcurrencyLeaser
from apps.gateway.engine.router import RoutingEngine
from apps.gateway.models.entities import Base, APIKey, Tenant, RoutingPolicy, Provider, ModelRoute

# Database engine initialization
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """Create tables if they do not exist and seed default policy."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default routing policy if not present
    async with async_session_maker() as session:
        result = await session.execute(
            select(RoutingPolicy).where(RoutingPolicy.alias == "auto/coding")
        )
        existing_policy = result.scalars().first()
        if not existing_policy:
            # Create default providers
            p_mock_a = Provider(
                name="mock-a",
                provider_type="mock",
                base_url=settings.MOCK_PROVIDER_URL,
                is_active=True,
            )
            p_mock_b = Provider(
                name="mock-b",
                provider_type="mock",
                base_url=settings.MOCK_PROVIDER_URL,
                is_active=True,
            )
            session.add_all([p_mock_a, p_mock_b])
            await session.flush()

            policy = RoutingPolicy(
                alias="auto/coding",
                description="Default auto coding policy routing between mock providers",
                max_retries=2,
                timeout_ms=5000,
            )
            session.add(policy)
            await session.flush()

            route_a = ModelRoute(
                policy_id=policy.id,
                provider_id=p_mock_a.id,
                upstream_model="mock-deterministic",
                priority=1,
                is_enabled=True,
            )
            route_b = ModelRoute(
                policy_id=policy.id,
                provider_id=p_mock_b.id,
                upstream_model="mock-deterministic",
                priority=2,
                is_enabled=True,
            )
            session.add_all([route_a, route_b])
            await session.commit()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


import logging

logger = logging.getLogger("crouter.deps")

# Shared instances for singletons / engines
_redis_client = None
_rate_limiter = None
_concurrency_leaser = None
_circuit_breaker = None
_routing_engine = None


async def init_redis():
    """Connect to Redis at startup or fallback based on REDIS_FALLBACK_IN_MEMORY."""
    global _redis_client, _rate_limiter, _concurrency_leaser, _circuit_breaker, _routing_engine
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            settings.REDIS_URL, decode_responses=True, socket_timeout=1.0
        )
        await client.ping()
        _redis_client = client
        logger.info("Successfully connected to Redis at %s", settings.REDIS_URL)
    except Exception as e:
        _redis_client = None
        if not settings.REDIS_FALLBACK_IN_MEMORY:
            logger.error(
                "Redis connection failed and REDIS_FALLBACK_IN_MEMORY=False: %s", e
            )
            raise RuntimeError(f"Redis is required but connection failed: {e}")
        logger.warning(
            "Redis unavailable at startup, using in-memory fallback (REDIS_FALLBACK_IN_MEMORY=True): %s",
            e,
        )

    # Instantiate singletons with active redis client (or None for fallback)
    _rate_limiter = RateLimiter(redis_client=_redis_client)
    _concurrency_leaser = ConcurrencyLeaser(redis_client=_redis_client)
    _circuit_breaker = CircuitBreaker(
        failure_threshold=settings.BREAKER_FAILURE_THRESHOLD,
        cooldown_seconds=settings.BREAKER_COOLDOWN_SECONDS,
        redis_client=_redis_client,
    )
    _routing_engine = RoutingEngine(circuit_breaker=_circuit_breaker)
    return _redis_client


async def close_redis():
    """Gracefully disconnect Redis pool on shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None


def reset_singletons(redis_client=None):
    """Helper to reset all singletons (used by tests for clean isolation)."""
    global _redis_client, _rate_limiter, _concurrency_leaser, _circuit_breaker, _routing_engine
    _redis_client = redis_client
    _rate_limiter = RateLimiter(redis_client=redis_client)
    _concurrency_leaser = ConcurrencyLeaser(redis_client=redis_client)
    _circuit_breaker = CircuitBreaker(
        failure_threshold=settings.BREAKER_FAILURE_THRESHOLD,
        cooldown_seconds=settings.BREAKER_COOLDOWN_SECONDS,
        redis_client=redis_client,
    )
    _routing_engine = RoutingEngine(circuit_breaker=_circuit_breaker)


async def get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_timeout=1.0
            )
            await client.ping()
            _redis_client = client
        except Exception:
            _redis_client = None
    return _redis_client


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(redis_client=_redis_client)
    return _rate_limiter


def get_concurrency_leaser() -> ConcurrencyLeaser:
    global _concurrency_leaser
    if _concurrency_leaser is None:
        _concurrency_leaser = ConcurrencyLeaser(redis_client=_redis_client)
    return _concurrency_leaser


def get_circuit_breaker() -> CircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker(
            failure_threshold=settings.BREAKER_FAILURE_THRESHOLD,
            cooldown_seconds=settings.BREAKER_COOLDOWN_SECONDS,
            redis_client=_redis_client,
        )
    return _circuit_breaker


def get_routing_engine() -> RoutingEngine:
    global _routing_engine
    if _routing_engine is None:
        _routing_engine = RoutingEngine(circuit_breaker=get_circuit_breaker())
    return _routing_engine


def hash_key(token: str) -> str:
    """Compute SHA-256 hash of API token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def get_authenticated_key(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """Validate Bearer gateway API key from Authorization header.

    Rejects missing or invalid keys fail-closed.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise InvalidAPIKeyError("Missing or invalid Authorization header format. Expected 'Bearer cr_live_...'")

    raw_token = authorization.replace("Bearer ", "").strip()
    if not raw_token:
        raise InvalidAPIKeyError("Authorization bearer token is empty.")

    key_hash = hash_key(raw_token)

    stmt = (
        select(APIKey)
        .where(APIKey.key_hash == key_hash)
        .options(selectinload(APIKey.tenant))
    )
    result = await db.execute(stmt)
    api_key = result.scalars().first()

    if not api_key:
        raise InvalidAPIKeyError("API key does not exist or has invalid hash.")

    if api_key.revoked_at is not None:
        raise InvalidAPIKeyError("API key has been revoked.")

    if api_key.tenant and not api_key.tenant.is_active:
        raise InvalidAPIKeyError("Tenant account is inactive.")

    return api_key
