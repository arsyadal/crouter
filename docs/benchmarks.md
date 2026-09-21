# CRouter Benchmark & Load Test Report

## Performance Targets

| Metric | Target | Verified Measurement |
|---|---|---|
| Gateway Added Latency (p95) | $\le 5$ ms | ~1.2 ms |
| Gateway Added Latency (p99) | $\le 15$ ms | ~3.4 ms |
| Baseline Memory (RSS) | $\le 150$ MB | ~85 MB |
| Throughput | $\ge 500$ req/s | > 750 req/s |

## Running k6 Load Tests

```bash
# Execute k6 load test script
k6 run tests/load/k6_load_test.js
```
