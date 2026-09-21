#!/usr/bin/env python3
"""
CRouter Latency & Throughput Benchmarking Utility.
Measures p50, p90, p95, p99 latency, concurrency limits, RPS, and error distribution.
"""
import sys
import os
import time
import asyncio
import argparse
import statistics
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()


async def send_worker(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    results: List[Dict[str, Any]],
):
    async with semaphore:
        t0 = time.perf_counter()
        try:
            res = await client.post(url, headers=headers, json=payload, timeout=30.0)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            gw_latency = res.headers.get("X-CRouter-Latency-Gateway-Ms")
            up_latency = res.headers.get("X-CRouter-Latency-Upstream-Ms")
            provider = res.headers.get("X-CRouter-Provider-Selected", "unknown")
            trace_id = res.headers.get("X-Trace-ID", "none")

            results.append({
                "status": res.status_code,
                "latency_ms": latency_ms,
                "gw_latency_ms": float(gw_latency) if gw_latency else None,
                "up_latency_ms": float(up_latency) if up_latency else None,
                "provider": provider,
                "trace_id": trace_id,
                "error": None if res.status_code == 200 else res.text[:120],
            })
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            results.append({
                "status": 0,
                "latency_ms": latency_ms,
                "gw_latency_ms": None,
                "up_latency_ms": None,
                "provider": "client_error",
                "trace_id": "none",
                "error": str(e),
            })


def calc_percentile(data: List[float], percentile: float) -> float:
    if not data:
        return 0.0
    k = (len(data) - 1) * (percentile / 100.0)
    f = int(k)
    c = f + 1
    if c < len(data):
        return data[f] + (data[c] - data[f]) * (k - f)
    return data[f]


async def run_benchmark(
    base_url: str,
    api_key: str,
    model: str,
    concurrency: int,
    total_requests: int,
    stream: bool,
):
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Benchmark ping. Reply with pong."},
        ],
        "max_tokens": 10,
        "stream": stream,
    }

    print("=" * 70)
    print(" CRouter Latency Benchmarking Suite")
    print("=" * 70)
    print(f" Target Endpoint   : {url}")
    print(f" Target Model      : {model}")
    print(f" Concurrency Level : {concurrency} parallel workers")
    print(f" Total Requests    : {total_requests}")
    print(f" SSE Streaming     : {stream}")
    print("-" * 70)
    print(" Warming up & dispatching benchmark load...")

    results: List[Dict[str, Any]] = []
    semaphore = asyncio.Semaphore(concurrency)

    wall_start = time.perf_counter()
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=concurrency + 5)) as client:
        tasks = [
            send_worker(client, semaphore, url, headers, payload, results)
            for _ in range(total_requests)
        ]
        await asyncio.gather(*tasks)

    total_time_s = time.perf_counter() - wall_start

    # Metrics calculation
    latencies = sorted([r["latency_ms"] for r in results])
    success_count = sum(1 for r in results if r["status"] == 200)
    failed_count = total_requests - success_count
    rps = total_requests / total_time_s if total_time_s > 0 else 0

    p50 = calc_percentile(latencies, 50.0)
    p90 = calc_percentile(latencies, 90.0)
    p95 = calc_percentile(latencies, 95.0)
    p99 = calc_percentile(latencies, 99.0)
    min_lat = latencies[0] if latencies else 0.0
    max_lat = latencies[-1] if latencies else 0.0
    avg_lat = statistics.mean(latencies) if latencies else 0.0

    print("\n" + "=" * 70)
    print(" BENCHMARK RESULTS SUMMARY")
    print("=" * 70)
    print(f" Total Elapsed Time  : {total_time_s:.2f} seconds")
    print(f" Throughput (RPS)    : {rps:.1f} req/sec")
    print(f" Successful Requests : {success_count} / {total_requests} ({(success_count/total_requests)*100:.1f}%)")
    print(f" Failed Requests     : {failed_count}")
    print("-" * 70)
    print(" LATENCY DISTRIBUTION (Gateway E2E):")
    print(f"   p50 (Median)      : {p50:8.2f} ms")
    print(f"   p90               : {p90:8.2f} ms")
    print(f"   p95               : {p95:8.2f} ms")
    print(f"   p99               : {p99:8.2f} ms")
    print(f"   Average           : {avg_lat:8.2f} ms")
    print(f"   Min / Max         : {min_lat:8.2f} ms / {max_lat:8.2f} ms")
    print("-" * 70)

    # Provider breakdown
    provider_counts: Dict[str, int] = {}
    for r in results:
        p = r["provider"]
        provider_counts[p] = provider_counts.get(p, 0) + 1

    print(" PROVIDER ROUTING BREAKDOWN:")
    for prov, cnt in sorted(provider_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {prov:<25}: {cnt} requests ({cnt/total_requests*100:.1f}%)")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="CRouter Latency & Throughput Benchmark")
    parser.add_argument("--url", default="http://localhost:8000", help="Gateway base URL")
    parser.add_argument("--key", default=os.getenv("TEST_API_KEY", "cr_live_demo1234567890abcdef"), help="Gateway API Key")
    parser.add_argument("--model", default="auto/coding", help="Model alias to test")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Concurrency workers")
    parser.add_argument("-n", "--requests", type=int, default=50, help="Total requests to dispatch")
    parser.add_argument("--stream", action="store_true", help="Use SSE streaming")

    args = parser.parse_args()
    asyncio.run(
        run_benchmark(
            base_url=args.url,
            api_key=args.key,
            model=args.model,
            concurrency=args.concurrency,
            total_requests=args.requests,
            stream=args.stream,
        )
    )


if __name__ == "__main__":
    main()
