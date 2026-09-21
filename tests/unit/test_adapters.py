import pytest
from apps.gateway.schemas.chat import ChatCompletionRequest, ChatMessage
from packages.adapters.mock import MockAdapter
from packages.adapters.gemini import GeminiAdapter
from packages.adapters.openrouter import OpenRouterAdapter


def test_mock_adapter_mapping():
    adapter = MockAdapter(provider_name="mock-a")
    assert adapter.validate_config() is True

    req = ChatCompletionRequest(
        model="auto/coding",
        messages=[
            ChatMessage(role="system", content="System prompt"),
            ChatMessage(role="user", content="User prompt"),
        ],
        temperature=0.8,
        max_tokens=256,
        stream=False,
    )

    mapped = adapter.map_request(req, "mock-deterministic")
    assert mapped["model"] == "mock-deterministic"
    assert len(mapped["messages"]) == 2
    assert mapped["temperature"] == 0.8
    assert mapped["max_tokens"] == 256
    assert mapped["stream"] is False


def test_gemini_adapter_mapping():
    adapter = GeminiAdapter(provider_name="gemini", api_key="dummy-gemini-key")
    assert adapter.validate_config() is True

    req = ChatCompletionRequest(
        model="gemini-1.5-flash",
        messages=[
            ChatMessage(role="system", content="System instruction"),
            ChatMessage(role="user", content="Hello Gemini"),
        ],
        temperature=0.5,
        max_tokens=100,
        stream=False,
    )

    mapped = adapter.map_request(req, "gemini-1.5-flash")
    assert "systemInstruction" in mapped
    assert mapped["systemInstruction"]["parts"][0]["text"] == "System instruction"
    assert len(mapped["contents"]) == 1
    assert mapped["contents"][0]["role"] == "user"
    assert mapped["contents"][0]["parts"][0]["text"] == "Hello Gemini"
    assert mapped["generationConfig"]["temperature"] == 0.5
    assert mapped["generationConfig"]["maxOutputTokens"] == 100


def test_openrouter_adapter_mapping():
    adapter = OpenRouterAdapter(provider_name="openrouter", api_key="sk-or-dummy")
    assert adapter.validate_config() is True

    req = ChatCompletionRequest(
        model="meta-llama/llama-3-70b-instruct",
        messages=[
            ChatMessage(role="user", content="Hello OpenRouter"),
        ],
        temperature=0.7,
        stream=True,
    )

    mapped = adapter.map_request(req, "meta-llama/llama-3-70b-instruct")
    assert mapped["model"] == "meta-llama/llama-3-70b-instruct"
    assert mapped["stream"] is True
    assert mapped["temperature"] == 0.7

    headers = adapter._get_headers()
    assert headers["Authorization"] == "Bearer sk-or-dummy"
    assert headers["HTTP-Referer"] == "https://github.com/arsyadal/crouter"
    assert headers["X-Title"] == "CRouter"


@pytest.mark.asyncio
async def test_gemini_adapter_multipart_response():
    import json
    import httpx
    from apps.gateway.schemas.chat import ChatCompletionRequest, ChatMessage

    # Mock response with multiple parts in content
    gemini_resp = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Part 1. "},
                        {"text": "Part 2."},
                    ],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 20,
            "totalTokenCount": 30,
        },
    }

    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json=gemini_resp)
    )
    mock_client = httpx.AsyncClient(transport=mock_transport)

    adapter = GeminiAdapter(
        provider_name="gemini",
        api_key="test-key",
        http_client=mock_client,
    )

    req = ChatCompletionRequest(
        model="gemini-1.5-flash",
        messages=[ChatMessage(role="user", content="Hi")],
    )

    resp = await adapter.send_completion(req, "gemini-1.5-flash")
    assert resp.choices[0].message.content == "Part 1. Part 2."
    assert resp.usage.total_tokens == 30
    await mock_client.aclose()


@pytest.mark.asyncio
async def test_openrouter_adapter_stream_error():
    import httpx
    from apps.gateway.core.errors import UpstreamProviderError
    from apps.gateway.schemas.chat import ChatCompletionRequest, ChatMessage

    # Mock stream returning an upstream error chunk
    sse_lines = (
        b'data: {"error": {"message": "Upstream model rate limit exceeded"}}\n\n'
    )
    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(200, content=sse_lines)
    )
    mock_client = httpx.AsyncClient(transport=mock_transport)

    adapter = OpenRouterAdapter(
        provider_name="openrouter",
        api_key="sk-or-test",
        http_client=mock_client,
    )

    req = ChatCompletionRequest(
        model="meta-llama/llama-3",
        messages=[ChatMessage(role="user", content="Hi")],
        stream=True,
    )

    with pytest.raises(UpstreamProviderError) as exc_info:
        async for _ in adapter.stream_completion(req, "meta-llama/llama-3"):
            pass

    assert "rate limit exceeded" in str(exc_info.value).lower()
    await mock_client.aclose()
