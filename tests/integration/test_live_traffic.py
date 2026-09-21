import os
import pytest
from packages.adapters.gemini import GeminiAdapter
from packages.adapters.openrouter import OpenRouterAdapter
from apps.gateway.schemas.chat import ChatCompletionRequest, ChatMessage

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()


@pytest.mark.skipif(not GEMINI_KEY, reason="Opt-in test: GEMINI_API_KEY not configured in environment")
@pytest.mark.asyncio
async def test_live_gemini_inference():
    adapter = GeminiAdapter(api_key=GEMINI_KEY, timeout_seconds=15.0)
    req = ChatCompletionRequest(
        model="gemini-1.5-flash",
        messages=[
            ChatMessage(role="user", content="Ping. Reply with 'pong'."),
        ],
        max_tokens=10,
    )
    res = await adapter.send_completion(req, target_model="gemini-1.5-flash")
    assert res.choices is not None
    assert len(res.choices) > 0
    assert len(res.choices[0].message.content) > 0


@pytest.mark.skipif(not OPENROUTER_KEY, reason="Opt-in test: OPENROUTER_API_KEY not configured in environment")
@pytest.mark.asyncio
async def test_live_openrouter_inference():
    adapter = OpenRouterAdapter(api_key=OPENROUTER_KEY, timeout_seconds=15.0)
    req = ChatCompletionRequest(
        model="meta-llama/llama-3.2-3b-instruct:free",
        messages=[
            ChatMessage(role="user", content="Ping. Reply with 'pong'."),
        ],
        max_tokens=10,
    )
    res = await adapter.send_completion(req, target_model="meta-llama/llama-3.2-3b-instruct:free")
    assert res.choices is not None
    assert len(res.choices) > 0
    assert len(res.choices[0].message.content) > 0


@pytest.mark.skipif(not GEMINI_KEY, reason="Opt-in test: GEMINI_API_KEY not configured in environment")
@pytest.mark.asyncio
async def test_live_gemini_streaming():
    adapter = GeminiAdapter(api_key=GEMINI_KEY, timeout_seconds=15.0)
    req = ChatCompletionRequest(
        model="gemini-1.5-flash",
        messages=[
            ChatMessage(role="user", content="Count from 1 to 3."),
        ],
        max_tokens=20,
        stream=True,
    )
    chunks = []
    async for chunk in adapter.stream_completion(req, target_model="gemini-1.5-flash"):
        if chunk.choices and chunk.choices[0].delta.content:
            chunks.append(chunk.choices[0].delta.content)
    assert len(chunks) > 0


@pytest.mark.skipif(not OPENROUTER_KEY, reason="Opt-in test: OPENROUTER_API_KEY not configured in environment")
@pytest.mark.asyncio
async def test_live_openrouter_streaming():
    adapter = OpenRouterAdapter(api_key=OPENROUTER_KEY, timeout_seconds=15.0)
    req = ChatCompletionRequest(
        model="meta-llama/llama-3.2-3b-instruct:free",
        messages=[
            ChatMessage(role="user", content="Count from 1 to 3."),
        ],
        max_tokens=20,
        stream=True,
    )
    chunks = []
    async for chunk in adapter.stream_completion(req, target_model="meta-llama/llama-3.2-3b-instruct:free"):
        if chunk.choices and chunk.choices[0].delta.content:
            chunks.append(chunk.choices[0].delta.content)
    assert len(chunks) > 0
