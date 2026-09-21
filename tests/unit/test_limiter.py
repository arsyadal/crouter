import pytest
from apps.gateway.engine.limiter import RateLimiter, ConcurrencyLeaser


@pytest.mark.asyncio
async def test_in_memory_rate_limiter():
    limiter = RateLimiter(redis_client=None)
    key = "tenant_test_key"
    limit = 3

    # First 3 allowed
    for _ in range(limit):
        allowed, retry_after = await limiter.check_rate_limit(key, limit_rpm=limit)
        assert allowed is True
        assert retry_after == 0

    # 4th disallowed
    allowed, retry_after = await limiter.check_rate_limit(key, limit_rpm=limit)
    assert allowed is False
    assert retry_after > 0


@pytest.mark.asyncio
async def test_in_memory_concurrency_leaser():
    leaser = ConcurrencyLeaser(redis_client=None)
    key = "tenant_concurrency"
    max_c = 2

    # Acquire 2
    ok1, count1 = await leaser.acquire(key, max_concurrency=max_c)
    assert ok1 is True
    assert count1 == 1

    ok2, count2 = await leaser.acquire(key, max_concurrency=max_c)
    assert ok2 is True
    assert count2 == 2

    # 3rd rejected
    ok3, count3 = await leaser.acquire(key, max_concurrency=max_c)
    assert ok3 is False

    # Release 1
    await leaser.release(key)
    ok4, count4 = await leaser.acquire(key, max_concurrency=max_c)
    assert ok4 is True
