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


@pytest.mark.asyncio
async def test_circuit_breaker_explicit_trip_and_reset():
    breaker = CircuitBreaker()
    route = "test-provider:test-model"

    assert await breaker.get_state(route) == CircuitState.CLOSED
    await breaker.trip(route)
    assert await breaker.get_state(route) == CircuitState.OPEN
    assert await breaker.can_execute(route) is False

    await breaker.reset(route)
    assert await breaker.get_state(route) == CircuitState.CLOSED
    assert await breaker.can_execute(route) is True


@pytest.mark.asyncio
async def test_circuit_breaker_redis_state_handling():
    # Mock Redis client storing strings
    class MockRedis:
        def __init__(self):
            self.store = {}

        async def get(self, key):
            return self.store.get(key)

        async def set(self, key, val):
            self.store[key] = str(val)

        async def delete(self, key):
            self.store.pop(key, None)

        async def incr(self, key):
            val = int(self.store.get(key, 0)) + 1
            self.store[key] = str(val)
            return val

        async def expire(self, key, ttl):
            pass

    mock_redis = MockRedis()
    breaker = CircuitBreaker(failure_threshold=2, redis_client=mock_redis)
    route = "redis-route"

    # Trip via failures
    await breaker.record_failure(route)
    await breaker.record_failure(route)
    assert await breaker.get_state(route) == CircuitState.OPEN
    # Verify stored as clean string
    assert mock_redis.store[f"crouter:breaker:{route}:state"] == "OPEN"

    # Reset
    await breaker.reset(route)
    assert await breaker.get_state(route) == CircuitState.CLOSED
    assert mock_redis.store[f"crouter:breaker:{route}:state"] == "CLOSED"
