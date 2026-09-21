# CRouter Operational Runbook

## Provisioning Keys

```bash
# Provision new key
crouter keys create --tenant "team-alpha" --rate-limit 120 --concurrency 10

# Revoke key
crouter keys revoke <prefix>
```

## Failure Diagnosis & Verification

### Circuit Breaker Tripped
If an upstream route returns consecutive 5xx errors or throttles:
1. Circuit breaker transitions to `OPEN`.
2. Traffic fails fast to secondary routes in the configured policy.
3. After `BREAKER_COOLDOWN_SECONDS` (default 30s), a canary request tests health in `HALF_OPEN`.

### Simulating Faults Locally
```bash
# Force mock-a to return 503
curl -X POST http://localhost:8001/mock/inject-fault?status=503&target=mock-a

# Reset all faults
curl -X POST http://localhost:8001/mock/reset
```
