import asyncio
import pytest
from apps.gateway.api.deps import get_rate_limiter, get_concurrency_leaser
from apps.gateway.core.config import settings
from apps.mock_provider.main import fault_registry
from tests.conftest import TEST_API_KEY, TEST_BURST_KEY


@pytest.mark.asyncio
async def test_rate_limit_burst_429(client):
    """TC-10: Exceeding RPM limit via HTTP returns HTTP 429 with Retry-After header."""
    headers = {"Authorization": f"Bearer {TEST_BURST_KEY}"}
    payload = {
        "model": "auto/coding",
        "messages": [{"role": "user", "content": "Rate limit burst test"}],
        "stream": False,
    }

    # Burst key has rate_limit_rpm = 2
    res1 = await client.post("/v1/chat/completions", headers=headers, json=payload)
    assert res1.status_code == 200

    res2 = await client.post("/v1/chat/completions", headers=headers, json=payload)
    assert res2.status_code == 200

    # 3rd request must be rejected with HTTP 429 and Retry-After
    res3 = await client.post("/v1/chat/completions", headers=headers, json=payload)
    assert res3.status_code == 429
    assert "retry-after" in res3.headers
    retry_after = int(res3.headers["retry-after"])
    assert retry_after > 0

    data = res3.json()
    assert data["error"]["code"] == "rate_limit_exceeded"
    assert data["error"]["type"] == "rate_limit_error"


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


@pytest.mark.asyncio
async def test_http_concurrency_ceiling_429(client):
    """TC-11 (HTTP): In-flight concurrent request exceeding max_concurrency=1 returns HTTP 429."""
    # Inject 150ms delay on mock-a so the first request stays in-flight
    fault_registry["mock-a"] = {"status": 200, "latency_ms": 150}

    headers = {"Authorization": f"Bearer {TEST_BURST_KEY}"}
    payload = {
        "model": "auto/coding",
        "messages": [{"role": "user", "content": "Concurrency test"}],
        "stream": False,
    }

    # Fire two concurrent requests
    task1 = asyncio.create_task(client.post("/v1/chat/completions", headers=headers, json=payload))
    # Slight micro-yield to ensure task1 starts and acquires lease
    await asyncio.sleep(0.01)
    task2 = asyncio.create_task(client.post("/v1/chat/completions", headers=headers, json=payload))

    res1, res2 = await asyncio.gather(task1, task2)
    statuses = [res1.status_code, res2.status_code]

    # One should succeed (200) and the other should be rejected by concurrency ceiling (429)
    assert 200 in statuses
    assert 429 in statuses


@pytest.mark.asyncio
async def test_redis_outage_fails_closed(client, monkeypatch):
    """TC-14: When REDIS_FALLBACK_IN_MEMORY=False and Redis is absent, gateway fails closed."""
    monkeypatch.setattr(settings, "REDIS_FALLBACK_IN_MEMORY", False)

    headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
    payload = {
        "model": "auto/coding",
        "messages": [{"role": "user", "content": "Outage test"}],
        "stream": False,
    }

    res = await client.post("/v1/chat/completions", headers=headers, json=payload)
    assert res.status_code == 500
    data = res.json()
    assert data["error"]["code"] == "redis_outage"
