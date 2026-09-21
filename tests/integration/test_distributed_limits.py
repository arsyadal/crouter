import asyncio
import pytest
from apps.gateway.api.deps import get_rate_limiter, get_concurrency_leaser
from tests.conftest import TEST_API_KEY


@pytest.mark.asyncio
async def test_rate_limit_burst_429(client):
    """TC-10: Exceeding RPM limit returns HTTP 429 with Retry-After header."""
    limiter = get_rate_limiter()
    # Force mock key to a low limit by exhausting it
    key_id = "test-rate-limit-key"
    limit = 5

    # Consume all 5 quota units
    for _ in range(limit):
        allowed, _ = await limiter.check_rate_limit(key_id, limit_rpm=limit)
        assert allowed is True

    # 6th request must be rejected
    allowed, retry_after = await limiter.check_rate_limit(key_id, limit_rpm=limit)
    assert allowed is False
    assert retry_after > 0


@pytest.mark.asyncio
async def test_concurrency_ceiling_lease(client):
    """TC-11: Exceeding max in-flight concurrency is capped and safely released."""
    leaser = get_concurrency_leaser()
    key_id = "test-concurrency-key"
    max_c = 2

    # Acquire 2 leases
    acq1, c1 = await leaser.acquire(key_id, max_concurrency=max_c)
    acq2, c2 = await leaser.acquire(key_id, max_concurrency=max_c)
    assert acq1 is True
    assert acq2 is True
    assert c2 == 2

    # 3rd lease must fail
    acq3, c3 = await leaser.acquire(key_id, max_concurrency=max_c)
    assert acq3 is False

    # Release 1 lease
    await leaser.release(key_id)

    # Now a 3rd lease can be acquired
    acq4, c4 = await leaser.acquire(key_id, max_concurrency=max_c)
    assert acq4 is True

    # Clean up
    await leaser.release(key_id)
    await leaser.release(key_id)
