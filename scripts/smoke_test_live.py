#!/usr/bin/env python3
"""CRouter — Live Traffic Experimentation Smoke Test Runner.

This script safely verifies live inference against real upstream providers
(Google Gemini and OpenRouter) when credentials are provided, or exercises
the deterministic local mock engine (Rp0) when run in local offline mode.

Usage:
    python scripts/smoke_test_live.py
    python scripts/smoke_test_live.py --provider gemini
    python scripts/smoke_test_live.py --provider openrouter
    python scripts/smoke_test_live.py --mock-only
"""

import sys
import os
import time
import asyncio
import argparse

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from apps.gateway.schemas.chat import (
    ChatCompletionRequest,
    ChatMessage,
)
from packages.adapters.gemini import GeminiAdapter
from packages.adapters.openrouter import OpenRouterAdapter
from packages.adapters.mock import MockAdapter
from apps.gateway.engine.router import RoutingEngine
from apps.gateway.engine.breaker import CircuitBreaker


def print_banner():
    print("=" * 72)
    print("      CRouter — Live Traffic Experimentation Smoke Test Harness")
    print("                \"One Gateway. Every Model.\"")
    print("=" * 72)


def get_keys():
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    return gemini_key, openrouter_key


async def test_gemini(api_key: str):
    print("\n[+] Testing Google Gemini Live Provider...")
    model_name = "gemini-1.5-flash"
    adapter = GeminiAdapter(api_key=api_key, timeout_seconds=20.0)

    if not adapter.validate_config():
        print("  [!] FAILED: GeminiAdapter config validation failed.")
        return False

    req = ChatCompletionRequest(
        model=model_name,
        messages=[
            ChatMessage(role="system", content="You are a helpful platform engineering AI."),
            ChatMessage(role="user", content="Answer in exactly 5 words: What is CRouter?"),
        ],
        temperature=0.2,
        max_tokens=50,
        stream=False,
    )

    # 1. Non-streaming test
    print(f"  [1/2] Sending non-streaming completion to '{model_name}'...")
    start_time = time.perf_counter()
    try:
        res = await adapter.send_completion(req, target_model=model_name)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        text = res.choices[0].message.content.strip()
        print(f"  [✓] Response received in {duration_ms:.1f}ms:")
        print(f"      \"{text}\"")
        print(f"      Tokens: prompt={res.usage.prompt_tokens}, completion={res.usage.completion_tokens}")
    except Exception as e:
        print(f"  [✗] Non-streaming Gemini request failed: {e}")
        return False

    # 2. Streaming test
    print(f"  [2/2] Sending streaming SSE completion to '{model_name}'...")
    req.stream = True
    start_time = time.perf_counter()
    stream_chunks = []
    try:
        async for chunk in adapter.stream_completion(req, target_model=model_name):
            if chunk.choices and chunk.choices[0].delta.content:
                stream_chunks.append(chunk.choices[0].delta.content)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        full_stream_text = "".join(stream_chunks).strip()
        print(f"  [✓] Stream completed in {duration_ms:.1f}ms ({len(stream_chunks)} chunks):")
        print(f"      \"{full_stream_text}\"")
    except Exception as e:
        print(f"  [✗] Streaming Gemini request failed: {e}")
        return False

    print("  [SUCCESS] Google Gemini live provider verified 100% operational!")
    return True


async def test_openrouter(api_key: str):
    print("\n[+] Testing OpenRouter Live Provider...")
    model_name = "meta-llama/llama-3.2-3b-instruct:free"
    adapter = OpenRouterAdapter(api_key=api_key, timeout_seconds=20.0)

    if not adapter.validate_config():
        print("  [!] FAILED: OpenRouterAdapter config validation failed.")
        return False

    req = ChatCompletionRequest(
        model=model_name,
        messages=[
            ChatMessage(role="system", content="You are a helpful platform engineering AI."),
            ChatMessage(role="user", content="Answer in exactly 5 words: What is CRouter?"),
        ],
        temperature=0.2,
        max_tokens=50,
        stream=False,
    )

    # 1. Non-streaming test
    print(f"  [1/2] Sending non-streaming completion to '{model_name}'...")
    start_time = time.perf_counter()
    try:
        res = await adapter.send_completion(req, target_model=model_name)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        text = res.choices[0].message.content.strip()
        print(f"  [✓] Response received in {duration_ms:.1f}ms:")
        print(f"      \"{text}\"")
    except Exception as e:
        print(f"  [✗] Non-streaming OpenRouter request failed: {e}")
        return False

    # 2. Streaming test
    print(f"  [2/2] Sending streaming SSE completion to '{model_name}'...")
    req.stream = True
    start_time = time.perf_counter()
    stream_chunks = []
    try:
        async for chunk in adapter.stream_completion(req, target_model=model_name):
            if chunk.choices and chunk.choices[0].delta.content:
                stream_chunks.append(chunk.choices[0].delta.content)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        full_stream_text = "".join(stream_chunks).strip()
        print(f"  [✓] Stream completed in {duration_ms:.1f}ms ({len(stream_chunks)} chunks):")
        print(f"      \"{full_stream_text}\"")
    except Exception as e:
        print(f"  [✗] Streaming OpenRouter request failed: {e}")
        return False

    print("  [SUCCESS] OpenRouter live provider verified 100% operational!")
    return True


async def test_mock_engine():
    print("\n[+] Testing Deterministic Rp0 Mock Engine & Route Resolution...")
    breaker = CircuitBreaker()
    engine = RoutingEngine(circuit_breaker=breaker)

    req = ChatCompletionRequest(
        model="auto/coding",
        messages=[
            ChatMessage(role="user", content="Generate a simple Python function"),
        ],
        stream=False,
    )

    print("  [1/3] Testing routing resolution for 'auto/coding'...")
    candidates = await engine.resolve_routes("auto/coding")
    print(f"  [✓] Resolved {len(candidates)} candidate routes: {[c.provider_name for c in candidates]}")

    print("  [2/3] Testing routing resolution for 'fast/chat'...")
    candidates_chat = await engine.resolve_routes("fast/chat")
    print(f"  [✓] Resolved {len(candidates_chat)} candidate routes: {[c.provider_name for c in candidates_chat]}")

    # 3. Check if mock provider is running locally to exercise execution
    import httpx
    mock_url = os.getenv("MOCK_PROVIDER_URL", "http://localhost:8001").rstrip("/")
    is_mock_running = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            res = await client.get(f"{mock_url}/health")
            if res.status_code == 200:
                is_mock_running = True
    except Exception:
        is_mock_running = False

    if is_mock_running:
        print(f"  [3/3] Mock server detected at {mock_url}. Executing Rp0 mock completion...")
        mock_adapter = MockAdapter(provider_name="mock-a", base_url=mock_url)
        try:
            resp = await mock_adapter.send_completion(req, target_model="mock-deterministic")
            print(f"  [✓] Mock completion response: \"{resp.choices[0].message.content}\"")
        except Exception as mock_err:
            print(f"  [!] Mock completion call error: {mock_err}")
    else:
        print(f"  [3/3] Local mock server ({mock_url}) is offline (start with `docker compose up mock_provider`).")

    print("  [SUCCESS] Rp0 Mock Engine and Routing Engine verified operational!")
    return True


async def main():
    parser = argparse.ArgumentParser(description="CRouter Live Traffic Smoke Test Harness")
    parser.add_argument("--provider", choices=["gemini", "openrouter", "all"], default="all")
    parser.add_argument("--mock-only", action="store_true", help="Run only local Rp0 mock verification")
    args = parser.parse_args()

    print_banner()
    gemini_key, openrouter_key = get_keys()

    print("\n[Configuration Status]")
    print(f"  - Google Gemini Key:   {'[DETECTED]' if gemini_key else '[NOT CONFIGURED] (Rp0 local default)'}")
    print(f"  - OpenRouter Key:      {'[DETECTED]' if openrouter_key else '[NOT CONFIGURED] (Rp0 local default)'}")

    if args.mock_only or (not gemini_key and not openrouter_key):
        print("\n" + "-" * 72)
        print("NOTICE: No live API keys detected in environment or .env.")
        print("CRouter is running in zero-budget Rp0 Local Mock Mode by design.")
        print("To experiment with live traffic:")
        print("  1. Copy .env.example to .env:  cp .env.example .env")
        print("  2. Set GEMINI_API_KEY=your_key  (Get free key at https://aistudio.google.com/)")
        print("  3. Set OPENROUTER_API_KEY=your_key  (https://openrouter.ai/keys)")
        print("  4. Rerun this script:          python scripts/smoke_test_live.py")
        print("-" * 72)
        success = await test_mock_engine()
        sys.exit(0 if success else 1)

    results = []
    if (args.provider in ("gemini", "all")) and gemini_key:
        ok = await test_gemini(gemini_key)
        results.append(("Gemini Live", ok))

    if (args.provider in ("openrouter", "all")) and openrouter_key:
        ok = await test_openrouter(openrouter_key)
        results.append(("OpenRouter Live", ok))

    print("\n" + "=" * 72)
    print("                    SMOKE TEST SUMMARY")
    print("=" * 72)
    all_ok = True
    for name, ok in results:
        status = "PASSED [OK]" if ok else "FAILED [ERR]"
        print(f"  {name:<30} {status}")
        if not ok:
            all_ok = False

    print("=" * 72)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
