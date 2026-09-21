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
