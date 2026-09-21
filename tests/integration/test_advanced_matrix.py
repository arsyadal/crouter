import json
import pytest
from click.testing import CliRunner
from apps.gateway.cli import cli
from apps.mock_provider.main import fault_registry
from tests.conftest import TEST_API_KEY


@pytest.mark.asyncio
async def test_primary_timeout_failover(client):
    """TC-08: When primary route times out, pre-stream failover routes to secondary."""
    # Inject 2000ms latency on mock-a (mock adapter will timeout or we can test timeout handling)
    # Or inject 504 / timeout simulation
    fault_registry["mock-a"] = {"status": 504, "latency_ms": 0}

    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Timeout failover test"}],
            "stream": False,
        },
    )

    assert res.status_code == 200
    assert res.headers.get("X-CRouter-Provider-Selected") == "mock-b"
    assert res.headers.get("X-CRouter-Attempts") == "2"


@pytest.mark.asyncio
async def test_mid_stream_disconnect(client):
    """TC-12: Mid-stream disconnection emits abort/error event and strictly prevents cross-provider failover."""
    fault_registry["mock-a"] = {
        "status": 200,
        "latency_ms": 0,
        "drop_after_chunks": 2,
    }

    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Mid stream drop test"}],
            "stream": True,
        },
    )

    assert res.status_code == 200
    # Stream began on mock-a
    assert res.headers.get("X-CRouter-Provider-Selected") == "mock-a"

    lines = [l.strip() for l in res.text.splitlines() if l.strip().startswith("data:")]
    # Should contain chunks and then interrupted error
    interrupted_found = any("upstream_stream_interrupted" in l for l in lines)
    assert interrupted_found is True
    # Crucial: [DONE] must NEVER be emitted when stream aborts mid-stream
    done_found = any("[DONE]" in l for l in lines)
    assert done_found is False


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(client):
    """FR-07: Metrics endpoint exports Prometheus counters, gauges, histogram, and breaker status."""
    # Send a request to generate metrics
    await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Metric generation test"}],
            "stream": False,
        },
    )

    res = await client.get("/metrics")
    assert res.status_code == 200
    text = res.text

    assert "crouter_http_requests_total" in text
    assert "crouter_active_in_flight_requests" in text
    assert "crouter_http_duration_seconds" in text


@pytest.mark.asyncio
async def test_mock_provider_control_plane():
    """FR-08: Mock provider control plane for programmable fault injection, status, and reset."""
    import httpx
    from httpx import ASGITransport
    from apps.mock_provider.main import app as mock_app

    transport = ASGITransport(app=mock_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://mock-provider") as c:
        # 1. Inject fault via query params alone
        res = await c.post("/mock/inject-fault?status=429&latency_ms=100")
        assert res.status_code == 200
        data = res.json()
        assert data["target"] == "mock-a"
        assert data["fault"]["status"] == 429
        assert data["fault"]["latency_ms"] == 100

        # 2. Check status
        res_status = await c.get("/mock/status")
        assert res_status.status_code == 200
        assert "mock-a" in res_status.json()["active_faults"]

        # 3. Reset
        res_reset = await c.post("/mock/reset")
        assert res_reset.status_code == 200
        assert res_reset.json()["active_faults"] == {}


def test_cli_key_lifecycle():
    """Verify CLI commands for key creation, listing, and revocation."""
    runner = CliRunner()

    # 1. Create key
    result_create = runner.invoke(
        cli, ["keys", "create", "--tenant", "test-agent", "--rate-limit", "90", "--concurrency", "8"]
    )
    assert result_create.exit_code == 0
    assert "cr_live_" in result_create.output
    assert "test-agent" in result_create.output

    # 2. List keys
    result_list = runner.invoke(cli, ["keys", "list"])
    assert result_list.exit_code == 0
    assert "90 RPM" in result_list.output
    assert "ACTIVE" in result_list.output

    # Extract prefix
    lines = result_list.output.splitlines()
    key_line = [l for l in lines if "90 RPM" in l][0]
    prefix = key_line.split()[0].replace("...", "")

    # 3. Revoke key
    result_revoke = runner.invoke(cli, ["keys", "revoke", prefix])
    assert result_revoke.exit_code == 0
    assert "Revoked 1 key" in result_revoke.output

    # 4. List keys again to verify status is REVOKED
    result_list_revoked = runner.invoke(cli, ["keys", "list"])
    assert result_list_revoked.exit_code == 0
    assert "REVOKED" in result_list_revoked.output
