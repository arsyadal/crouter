import pytest
import asyncio
from apps.gateway.engine.breaker import CircuitBreaker, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_transitions():
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.1)
    route = "mock-route"

    # Initially closed
    assert await breaker.get_state(route) == CircuitState.CLOSED
    assert await breaker.can_execute(route) is True

    # 1st failure
    await breaker.record_failure(route)
    assert await breaker.get_state(route) == CircuitState.CLOSED

    # 2nd failure
    await breaker.record_failure(route)
    assert await breaker.get_state(route) == CircuitState.CLOSED

    # 3rd failure: trips to OPEN!
    await breaker.record_failure(route)
    assert await breaker.get_state(route) == CircuitState.OPEN
    assert await breaker.can_execute(route) is False

    # Wait for cooldown to expire
    await asyncio.sleep(0.12)

    # State transitions to HALF_OPEN (allows canary)
    assert await breaker.get_state(route) == CircuitState.HALF_OPEN
    assert await breaker.can_execute(route) is True

    # Successful canary closes the breaker
    await breaker.record_success(route)
    assert await breaker.get_state(route) == CircuitState.CLOSED
    assert await breaker.can_execute(route) is True
