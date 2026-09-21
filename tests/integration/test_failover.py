import json
import pytest
from apps.mock_provider.main import fault_registry
from tests.conftest import TEST_API_KEY


@pytest.mark.asyncio
async def test_pre_stream_failover_503(client):
    """TC-06: When primary provider mock-a throws 503, gateway fails over to mock-b."""
    # Inject fault on primary target mock-a
    fault_registry["mock-a"] = {"status": 503, "latency_ms": 0}

    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Test failover resilience"}],
            "stream": False,
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "chat.completion"
    # Proves automated failover to mock-b occurred!
    assert res.headers.get("X-CRouter-Provider-Selected") == "mock-b"
    assert res.headers.get("X-CRouter-Attempts") == "2"


@pytest.mark.asyncio
async def test_pre_stream_failover_429(client):
    """TC-07: When primary provider mock-a throws 429, gateway fails over to mock-b."""
    fault_registry["mock-a"] = {"status": 429, "latency_ms": 0}

    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Test 429 failover"}],
            "stream": False,
        },
    )

    assert res.status_code == 200
    assert res.headers.get("X-CRouter-Provider-Selected") == "mock-b"
    assert res.headers.get("X-CRouter-Attempts") == "2"


@pytest.mark.asyncio
async def test_all_routes_unavailable_503(client):
    """TC-09: When all configured routes fail, returns 503 no_healthy_route."""
    fault_registry["mock-a"] = {"status": 503, "latency_ms": 0}
    fault_registry["mock-b"] = {"status": 503, "latency_ms": 0}

    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "All routes down"}],
            "stream": False,
        },
    )

    assert res.status_code == 503
    data = res.json()
    assert data["error"]["code"] == "no_healthy_route"


@pytest.mark.asyncio
async def test_streaming_pre_stream_failover(client):
    """Streaming failover works before the first chunk is emitted."""
    fault_registry["mock-a"] = {"status": 503, "latency_ms": 0}

    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Streaming failover test"}],
            "stream": True,
        },
    )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    assert res.headers.get("X-CRouter-Provider-Selected") == "mock-b"
    assert res.headers.get("X-CRouter-Attempts") == "2"
