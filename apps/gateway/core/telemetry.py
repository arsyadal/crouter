import time
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("crouter.telemetry")


class SimpleMetrics:
    """Prometheus-compatible metrics accumulator supporting counters, gauges, histograms, and breaker status."""

    def __init__(self):
        # Key: (model, provider, status_code) -> count
        self.requests_total: Dict[Tuple[str, str, int], int] = {}
        # Key: tenant_id -> count
        self.active_in_flight: Dict[str, int] = {}
        # Latency samples in seconds
        self.durations_seconds: List[float] = []
        # Key: (route_id, state) -> 1 or 0
        self.circuit_breaker_states: Dict[Tuple[str, str], int] = {}

    def inc_request(self, model: str, provider: str, status_code: int):
        key = (str(model), str(provider), int(status_code))
        self.requests_total[key] = self.requests_total.get(key, 0) + 1

    def observe_duration(self, seconds: float):
        self.durations_seconds.append(float(seconds))
        if len(self.durations_seconds) > 2000:
            self.durations_seconds.pop(0)

    def set_in_flight(self, tenant_id: str, count: int):
        self.active_in_flight[str(tenant_id)] = max(0, int(count))

    def set_circuit_breaker_status(self, route_id: str, state: str):
        for s in ("CLOSED", "OPEN", "HALF_OPEN"):
            self.circuit_breaker_states[(route_id, s)] = 1 if s == state else 0

    def reset(self):
        """Reset metrics state for isolated test verification."""
        self.requests_total.clear()
        self.active_in_flight.clear()
        self.durations_seconds.clear()
        self.circuit_breaker_states.clear()

    def export_prometheus(self) -> str:
        lines: List[str] = [
            "# HELP crouter_http_requests_total Total HTTP requests processed by CRouter",
            "# TYPE crouter_http_requests_total counter",
        ]
        for (model, provider, status), count in sorted(self.requests_total.items()):
            lines.append(
                f'crouter_http_requests_total{{model="{model}",provider="{provider}",status_code="{status}"}} {count}'
            )

        lines.extend([
            "# HELP crouter_active_in_flight_requests Active in-flight requests",
            "# TYPE crouter_active_in_flight_requests gauge",
        ])
        for tenant_id, count in sorted(self.active_in_flight.items()):
            lines.append(
                f'crouter_active_in_flight_requests{{tenant_id="{tenant_id}"}} {count}'
            )

        if self.circuit_breaker_states:
            lines.extend([
                "# HELP crouter_circuit_breaker_status Circuit breaker state per route (1=active, 0=inactive)",
                "# TYPE crouter_circuit_breaker_status gauge",
            ])
            for (route_id, state), val in sorted(self.circuit_breaker_states.items()):
                lines.append(
                    f'crouter_circuit_breaker_status{{route_id="{route_id}",state="{state}"}} {val}'
                )

        # Durations histogram
        buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        lines.extend([
            "# HELP crouter_http_duration_seconds HTTP request duration in seconds",
            "# TYPE crouter_http_duration_seconds histogram",
        ])
        total_count = len(self.durations_seconds)
        total_sum = sum(self.durations_seconds) if total_count > 0 else 0.0

        for b in buckets:
            b_count = sum(1 for d in self.durations_seconds if d <= b)
            lines.append(f'crouter_http_duration_seconds_bucket{{le="{b}"}} {b_count}')
        lines.append(f'crouter_http_duration_seconds_bucket{{le="+Inf"}} {total_count}')
        lines.append(f'crouter_http_duration_seconds_sum {total_sum:.6f}')
        lines.append(f'crouter_http_duration_seconds_count {total_count}')

        return "\n".join(lines) + "\n"


metrics = SimpleMetrics()


def scrub_sensitive_data(headers_or_payload: Any) -> Any:
    """Scrub Authorization tokens, prompts, completions, and secrets."""
    if isinstance(headers_or_payload, dict):
        scrubbed = {}
        for k, v in headers_or_payload.items():
            k_lower = str(k).lower()
            if any(
                secret_word in k_lower
                for secret_word in ("authorization", "token", "secret", "key", "password")
            ):
                scrubbed[k] = "[REDACTED]"
            elif k_lower in ("messages", "prompt", "content"):
                scrubbed[k] = "[REDACTED_PROMPT_PAYLOAD]"
            elif isinstance(v, (dict, list)):
                scrubbed[k] = scrub_sensitive_data(v)
            else:
                scrubbed[k] = v
        return scrubbed
    elif isinstance(headers_or_payload, list):
        return [scrub_sensitive_data(item) for item in headers_or_payload]
    return headers_or_payload
