import pytest
import httpx


@pytest.mark.asyncio
async def test_full_admin_dashboard_and_inference_lifecycle(client: httpx.AsyncClient):
    # 1. Probes
    live_res = await client.get("/health/live")
    assert live_res.status_code == 200

    ready_res = await client.get("/health/ready")
    assert ready_res.status_code == 200

    # 2. Overview metrics
    ov_res = await client.get("/admin/overview")
    assert ov_res.status_code == 200
    ov_data = ov_res.json()
    assert ov_data["total_policies"] >= 2
    assert ov_data["total_routes"] >= 4
    assert ov_data["gateway_version"] is not None

    # 3. Route discovery and circuit breaker state
    routes_res = await client.get("/admin/routes")
    assert routes_res.status_code == 200
    routes_data = routes_res.json()["data"]
    assert len(routes_data) >= 2

    # Verify both auto/coding and fast/chat exist
    aliases = {p["alias"] for p in routes_data}
    assert "auto/coding" in aliases
    assert "fast/chat" in aliases

    # 4. Breaker Trip & Reset on a route
    target_route = routes_data[0]["routes"][0]["route_key"]
    trip_res = await client.post("/admin/breaker/trip", json={"route_key": target_route})
    assert trip_res.status_code == 200
    assert trip_res.json()["breaker_state"] == "OPEN"

    reset_res = await client.post("/admin/breaker/reset", json={"route_key": target_route})
    assert reset_res.status_code == 200
    assert reset_res.json()["breaker_state"] == "CLOSED"

    # 5. API Key Governance Lifecycle: Create -> Verify -> Revoke
    key_create_res = await client.post(
        "/admin/keys",
        json={"tenant": "e2e-governance-tenant", "rate_limit_rpm": 90, "max_concurrency": 15},
    )
    assert key_create_res.status_code == 201
    created_key_data = key_create_res.json()
    raw_token = created_key_data["key"]
    key_id = created_key_data["id"]

    # 6. Execute Non-Streaming Completion with new key
    infer_res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {raw_token}"},
        json={
            "model": "auto/coding",
            "messages": [
                {"role": "system", "content": "You are a test assistant."},
                {"role": "user", "content": "Hello gateway!"},
            ],
            "stream": False,
        },
    )
    assert infer_res.status_code == 200
    assert infer_res.headers.get("X-CRouter-Provider-Selected") in ("mock-a", "mock-b")
    assert infer_res.headers.get("X-CRouter-Latency-Gateway-Ms") is not None
    assert infer_res.headers.get("X-CRouter-Latency-Upstream-Ms") is not None

    # 7. Execute Streaming Completion with new key & verify stream headers
    stream_res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {raw_token}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Stream me a response"}],
            "stream": True,
        },
    )
    assert stream_res.status_code == 200
    assert stream_res.headers.get("Content-Type") == "text/event-stream"
    assert stream_res.headers.get("X-CRouter-Provider-Selected") in ("mock-a", "mock-b")
    assert stream_res.headers.get("X-CRouter-Latency-Gateway-Ms") is not None
    assert "data:" in stream_res.text
    assert "data: [DONE]" in stream_res.text

    # 8. Revoke Key and verify immediate fail-closed rejection
    revoke_res = await client.post(f"/admin/keys/{key_id}/revoke")
    assert revoke_res.status_code == 200
    assert revoke_res.json()["is_active"] is False

    rejected_res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {raw_token}"},
        json={"model": "auto/coding", "messages": [{"role": "user", "content": "Hello"}]},
    )
    assert rejected_res.status_code == 401

    # 9. Verify Visual Dashboard HTML endpoints
    dash_res = await client.get("/dashboard")
    assert dash_res.status_code == 200
    assert "<!DOCTYPE html>" in dash_res.text
    assert "CRouter Gateway" in dash_res.text

    root_res = await client.get("/")
    assert root_res.status_code == 200
    assert "<!DOCTYPE html>" in root_res.text
