import json
import pytest
from tests.conftest import TEST_API_KEY, TEST_REVOKED_KEY


@pytest.mark.asyncio
async def test_anthropic_messages_non_streaming(client):
    res = await client.post(
        "/v1/messages",
        headers={
            "x-api-key": TEST_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": "auto/coding",
            "messages": [
                {"role": "user", "content": "Write hello world in python"},
            ],
            "max_tokens": 256,
            "system": "You are an expert Python engineer.",
            "stream": False,
        },
    )
    assert res.status_code == 200
    data = res.json()

    # Anthropic contract validation
    assert data["type"] == "message"
    assert data["role"] == "assistant"
    assert data["model"] == "auto/coding"
    assert len(data["content"]) > 0
    assert data["content"][0]["type"] == "text"
    assert len(data["content"][0]["text"]) > 0
    assert data["stop_reason"] == "end_turn"
    assert data["usage"]["input_tokens"] > 0
    assert data["usage"]["output_tokens"] > 0

    # Diagnostic headers
    assert "X-CRouter-Request-ID" in res.headers
    assert res.headers.get("X-CRouter-Provider-Selected") == "mock-a"
    assert "X-CRouter-Tokens-Saved" in res.headers
    assert res.headers.get("anthropic-version") == "2023-06-01"


@pytest.mark.asyncio
async def test_anthropic_messages_streaming_sse(client):
    res = await client.post(
        "/v1/messages",
        headers={
            "Authorization": f"Bearer {TEST_API_KEY}",
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": "auto/coding",
            "messages": [
                {"role": "user", "content": "Stream response test"},
            ],
            "max_tokens": 128,
            "stream": True,
        },
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    events = []
    current_event = None

    for line in res.text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("event:"):
            current_event = line.replace("event:", "").strip()
        elif line.startswith("data:") and current_event:
            payload = json.loads(line.replace("data:", "").strip())
            events.append((current_event, payload))
            current_event = None

    event_types = [e[0] for e in events]
    assert "message_start" in event_types
    assert "content_block_start" in event_types
    assert "content_block_delta" in event_types
    assert "content_block_stop" in event_types
    assert "message_delta" in event_types
    assert "message_stop" in event_types

    # Inspect text delta content
    deltas = [e[1] for e in events if e[0] == "content_block_delta"]
    assert len(deltas) > 0
    assert deltas[0]["delta"]["type"] == "text_delta"


@pytest.mark.asyncio
async def test_anthropic_structured_content_blocks_and_system(client):
    res = await client.post(
        "/v1/messages",
        headers={"x-api-key": TEST_API_KEY},
        json={
            "model": "auto/coding",
            "system": [
                {"type": "text", "text": "System instructions part 1."},
                {"type": "text", "text": "System instructions part 2."},
            ],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Here is the code context."},
                        {"type": "tool_result", "content": "Tool exit code 0."},
                    ],
                }
            ],
            "max_tokens": 100,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "message"
    assert len(data["content"][0]["text"]) > 0


@pytest.mark.asyncio
async def test_anthropic_auth_rejection(client):
    # Missing auth
    res_missing = await client.post(
        "/v1/messages",
        json={"model": "auto/coding", "messages": [{"role": "user", "content": "Hi"}]},
    )
    assert res_missing.status_code == 401

    # Revoked key
    res_revoked = await client.post(
        "/v1/messages",
        headers={"x-api-key": TEST_REVOKED_KEY},
        json={"model": "auto/coding", "messages": [{"role": "user", "content": "Hi"}]},
    )
    assert res_revoked.status_code == 401


@pytest.mark.asyncio
async def test_anthropic_claude_model_route(client):
    res = await client.post(
        "/v1/messages",
        headers={"x-api-key": TEST_API_KEY},
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": "Hello Claude Code"}],
            "max_tokens": 50,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "message"


@pytest.mark.asyncio
async def test_anthropic_token_saver_and_bypass_header(client):
    # Request with bloated ANSI terminal text
    bloated_text = "\x1b[31mFAIL\x1b[0m test line\n\n\n\n" + "Identical warning\n" * 10

    # 1. Default: Token Saver active
    res_opt = await client.post(
        "/v1/messages",
        headers={"x-api-key": TEST_API_KEY},
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": bloated_text}],
            "max_tokens": 50,
        },
    )
    assert res_opt.status_code == 200
    saved_tokens = int(res_opt.headers.get("X-CRouter-Tokens-Saved", "0"))
    assert saved_tokens > 0

    # 2. Bypass header: X-CRouter-Token-Saver: off
    res_bypass = await client.post(
        "/v1/messages",
        headers={
            "x-api-key": TEST_API_KEY,
            "X-CRouter-Token-Saver": "off",
        },
        json={
            "model": "auto/coding",
            "messages": [{"role": "user", "content": bloated_text}],
            "max_tokens": 50,
        },
    )
    assert res_bypass.status_code == 200
    bypass_saved = int(res_bypass.headers.get("X-CRouter-Tokens-Saved", "0"))
    assert bypass_saved == 0
