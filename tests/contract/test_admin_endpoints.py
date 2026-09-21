import pytest
import httpx


@pytest.mark.asyncio
async def test_admin_overview(client: httpx.AsyncClient):
    res = await client.get("/admin/overview")
    assert res.status_code == 200
    data = res.json()
    assert "total_keys" in data
    assert "active_keys" in data
    assert "total_policies" in data
    assert "open_breakers_count" in data
    assert "gateway_version" in data


@pytest.mark.asyncio
async def test_admin_keys_crud(client: httpx.AsyncClient):
    # 1. List keys
    res = await client.get("/admin/keys")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    initial_count = len(data["data"])

    # 2. Create new key
    create_res = await client.post(
        "/admin/keys",
        json={
            "tenant": "dashboard-test-tenant",
            "rate_limit_rpm": 100,
            "max_concurrency": 25,
        },
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["tenant"] == "dashboard-test-tenant"
    assert created["rate_limit_rpm"] == 100
    assert created["max_concurrency"] == 25
    assert created["key"].startswith("cr_live_")
    key_id = created["id"]

    # 3. List keys again to verify created
    res2 = await client.get("/admin/keys")
    data2 = res2.json()
    assert len(data2["data"]) == initial_count + 1

    # 4. Revoke key
    revoke_res = await client.post(f"/admin/keys/{key_id}/revoke")
    assert revoke_res.status_code == 200
    revoked = revoke_res.json()
    assert revoked["is_active"] is False
    assert revoked["revoked_at"] is not None


@pytest.mark.asyncio
async def test_admin_routes_and_breaker(client: httpx.AsyncClient):
    # 1. List routes
    res = await client.get("/admin/routes")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    assert len(data["data"]) >= 1
    policy = data["data"][0]
    assert "alias" in policy
    assert "routes" in policy
    assert len(policy["routes"]) >= 1

    route_key = policy["routes"][0]["route_key"]

    # 2. Trip breaker for this route
    trip_res = await client.post("/admin/breaker/trip", json={"route_key": route_key})
    assert trip_res.status_code == 200
    trip_data = trip_res.json()
    assert trip_data["breaker_state"] == "OPEN"

    # Verify route status reflects OPEN
    res_after_trip = await client.get("/admin/routes")
    data_after = res_after_trip.json()
    matching = [
        r
        for p in data_after["data"]
        for r in p["routes"]
        if r["route_key"] == route_key
    ]
    assert matching[0]["breaker_state"] == "OPEN"

    # 3. Reset breaker
    reset_res = await client.post("/admin/breaker/reset", json={"route_key": route_key})
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["breaker_state"] == "CLOSED"


@pytest.mark.asyncio
async def test_dashboard_ui_endpoint(client: httpx.AsyncClient):
    res = await client.get("/dashboard")
    assert res.status_code == 200
    assert "CRouter Gateway" in res.text
    assert "Routing Policies & Circuit Breakers" in res.text

    res_root = await client.get("/")
    assert res_root.status_code == 200
    assert "CRouter Gateway" in res_root.text


@pytest.mark.asyncio
async def test_admin_keys_validation_and_conflicts(client: httpx.AsyncClient):
    # 1. Empty/whitespace tenant rejection
    res_empty = await client.post(
        "/admin/keys",
        json={"tenant": "   ", "rate_limit_rpm": 60, "max_concurrency": 10},
    )
    assert res_empty.status_code == 400

    # 2. Duplicate explicit key conflict
    explicit_token = "cr_live_custom_token_unique_123"
    res1 = await client.post(
        "/admin/keys",
        json={"tenant": "tenant-dup-test", "key": explicit_token},
    )
    assert res1.status_code == 201

    res_dup = await client.post(
        "/admin/keys",
        json={"tenant": "tenant-dup-test-2", "key": explicit_token},
    )
    assert res_dup.status_code == 409

    # 3. Revoke non-existent key
    res_nf = await client.post("/admin/keys/non-existent-key-uuid-1234/revoke")
    assert res_nf.status_code == 404


@pytest.mark.asyncio
async def test_admin_breaker_validation(client: httpx.AsyncClient):
    # Empty route key rejection
    res_empty_trip = await client.post("/admin/breaker/trip", json={"route_key": "   "})
    assert res_empty_trip.status_code == 400

    res_empty_reset = await client.post("/admin/breaker/reset", json={"route_key": "   "})
    assert res_empty_reset.status_code == 400

