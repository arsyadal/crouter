import json
import pytest
from tests.conftest import TEST_API_KEY, TEST_REVOKED_KEY


@pytest.mark.asyncio
async def test_health_live(client):
    res = await client.get("/health/live")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready(client):
    res = await client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"


@pytest.mark.asyncio
async def test_models_list(client):
    res = await client.get(
        "/v1/models",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "list"
    model_ids = [m["id"] for m in data["data"]]
    assert "auto/coding" in model_ids


@pytest.mark.asyncio
async def test_auth_missing_key(client):
    res = await client.post(
        "/v1/chat/completions",
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "invalid_api_key"


@pytest.mark.asyncio
async def test_auth_revoked_key(client):
    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_REVOKED_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "invalid_api_key"
    assert "revoked" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_unsupported_parameter(client):
    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Hello"}],
            "logprobs": True,  # Unsupported parameter
        },
    )
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "invalid_request_error"


@pytest.mark.asyncio
async def test_unknown_model_alias(client):
    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "unknown/nonexistent-model",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "model_not_found"


@pytest.mark.asyncio
async def test_chat_completion_non_streaming(client):
    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [
                {"role": "system", "content": "You are a test assistant"},
                {"role": "user", "content": "Explain circuit breakers"},
            ],
            "stream": False,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert len(data["choices"][0]["message"]["content"]) > 0
    assert data["usage"]["total_tokens"] > 0
    # Verify diagnostic headers
    assert "X-CRouter-Request-ID" in res.headers
    assert res.headers.get("X-CRouter-Provider-Selected") == "mock-a"
    assert res.headers.get("X-CRouter-Attempts") == "1"


@pytest.mark.asyncio
async def test_chat_completion_streaming(client):
    res = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": "Hello streaming"}],
            "stream": True,
        },
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    assert res.headers.get("X-CRouter-Provider-Selected") == "mock-a"

    chunks = []
    has_done = False
    for line in res.text.splitlines():
        line = line.strip()
        if not line or not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if data_str == "[DONE]":
            has_done = True
            break
        chunk = json.loads(data_str)
        chunks.append(chunk)

    assert has_done is True
    assert len(chunks) > 0
    assert chunks[0]["object"] == "chat.completion.chunk"
