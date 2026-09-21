import asyncio
import hashlib
from datetime import datetime, timezone
import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from apps.gateway.api.deps import get_db, get_routing_engine, init_db
from apps.gateway.engine.breaker import CircuitBreaker
from apps.gateway.engine.router import RoutingEngine
from apps.gateway.main import app
from apps.gateway.models.entities import Base, Tenant, APIKey, Provider, RoutingPolicy, ModelRoute
from apps.mock_provider.main import app as mock_app, fault_registry
from packages.adapters.mock import MockAdapter

TEST_API_KEY = "cr_live_testkey12345678901234567890"
TEST_REVOKED_KEY = "cr_live_revokedkey1234567890123456"
TEST_BURST_KEY = "cr_live_burstkey1234567890123456789"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed test tenant and API keys
    async with async_session() as session:
        t = Tenant(name="test-tenant", is_active=True)
        session.add(t)
        await session.flush()

        k_valid = APIKey(
            tenant_id=t.id,
            key_hash=hashlib.sha256(TEST_API_KEY.encode()).hexdigest(),
            key_prefix=TEST_API_KEY[:12],
            rate_limit_rpm=60,
            max_concurrency=10,
        )
        k_revoked = APIKey(
            tenant_id=t.id,
            key_hash=hashlib.sha256(TEST_REVOKED_KEY.encode()).hexdigest(),
            key_prefix=TEST_REVOKED_KEY[:12],
            rate_limit_rpm=60,
            max_concurrency=10,
            revoked_at=datetime.now(timezone.utc),
        )
        k_burst = APIKey(
            tenant_id=t.id,
            key_hash=hashlib.sha256(TEST_BURST_KEY.encode()).hexdigest(),
            key_prefix=TEST_BURST_KEY[:12],
            rate_limit_rpm=2,
            max_concurrency=1,
        )
        session.add_all([k_valid, k_revoked, k_burst])

        # Seed mock-a, mock-b and auto/coding policy
        p_mock_a = Provider(
            name="mock-a",
            provider_type="mock",
            base_url="http://mock-provider",
            is_active=True,
        )
        p_mock_b = Provider(
            name="mock-b",
            provider_type="mock",
            base_url="http://mock-provider",
            is_active=True,
        )
        session.add_all([p_mock_a, p_mock_b])
        await session.flush()

        policy = RoutingPolicy(
            alias="auto/coding",
            description="Auto coding priority route",
            max_retries=2,
            timeout_ms=5000,
        )
        session.add(policy)
        await session.flush()

        r_a = ModelRoute(
            policy_id=policy.id,
            provider_id=p_mock_a.id,
            upstream_model="mock-deterministic",
            priority=1,
            is_enabled=True,
        )
        r_b = ModelRoute(
            policy_id=policy.id,
            provider_id=p_mock_b.id,
            upstream_model="mock-deterministic",
            priority=2,
            is_enabled=True,
        )
        session.add_all([r_a, r_b])

        await session.commit()

    yield async_session

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    fault_registry.clear()

    # Create mock transport for adapters
    mock_transport = ASGITransport(app=mock_app)
    mock_http_client = httpx.AsyncClient(
        transport=mock_transport, base_url="http://mock-provider"
    )

    # Set up routing engine with mock adapters using this mock transport
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=2.0)
    adapter_mock_a = MockAdapter(
        provider_name="mock-a",
        base_url="http://mock-provider",
        http_client=mock_http_client,
    )
    adapter_mock_b = MockAdapter(
        provider_name="mock-b",
        base_url="http://mock-provider",
        http_client=mock_http_client,
    )

    routing_engine = RoutingEngine(
        circuit_breaker=breaker,
        adapter_overrides={
            "mock-a": adapter_mock_a,
            "mock-b": adapter_mock_b,
        },
    )

    async def override_get_db():
        async with test_db() as session:
            yield session

    import apps.gateway.api.deps as deps
    from apps.gateway.core.telemetry import metrics

    metrics.reset()
    deps.reset_singletons()

    app.dependency_overrides[deps.get_db] = override_get_db
    deps._routing_engine = routing_engine
    deps._circuit_breaker = breaker

    gateway_transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=gateway_transport, base_url="http://testserver"
    ) as c:
        yield c

    app.dependency_overrides.clear()
    deps.reset_singletons()
    metrics.reset()
    await mock_http_client.aclose()
