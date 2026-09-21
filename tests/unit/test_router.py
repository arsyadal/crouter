import pytest
from apps.gateway.engine.breaker import CircuitBreaker
from apps.gateway.engine.router import RoutingEngine
from apps.gateway.core.errors import ModelNotFoundError


@pytest.mark.asyncio
async def test_resolve_default_routes():
    breaker = CircuitBreaker()
    engine = RoutingEngine(circuit_breaker=breaker)

    candidates = await engine.resolve_routes("auto/coding")
    assert len(candidates) == 2
    assert candidates[0].provider_name == "mock-a"
    assert candidates[0].priority == 1
    assert candidates[1].provider_name == "mock-b"
    assert candidates[1].priority == 2


@pytest.mark.asyncio
async def test_resolve_unknown_route():
    breaker = CircuitBreaker()
    engine = RoutingEngine(circuit_breaker=breaker)

    with pytest.raises(ModelNotFoundError):
        await engine.resolve_routes("totally-unknown-model-xyz")
