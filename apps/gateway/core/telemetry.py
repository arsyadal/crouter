import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("crouter.telemetry")


class SimpleMetrics:
    """Zero-dependency Prometheus-style metrics accumulator."""

    def __init__(self):
        self.requests_total: Dict[str, int] = {}
        self.active_in_flight: Dict[str, int] = {}
        self.durations_seconds: list[float] = []

    def inc_request(self, model: str, provider: str, status_code: int):
        key = f'{model}_{provider}_{status_code}'
        self.requests_total[key] = self.requests_total.get(key, 0) + 1

    def observe_duration(self, seconds: float):
        self.durations_seconds.append(seconds)
        if len(self.durations_seconds) > 1000:
            self.durations_seconds.pop(0)

    def set_in_flight(self, tenant_id: str, count: int):
        self.active_in_flight[tenant_id] = count

    def export_prometheus(self) -> str:
        lines = [
            "# HELP crouter_http_requests_total Total HTTP requests processed by CRouter",
            "# TYPE crouter_http_requests_total counter",
        ]
        for key, count in self.requests_total.items():
            parts = key.split("_")
            model, provider, status = parts[0], parts[1], parts[2]
            lines.append(
                f'crouter_http_requests_total{{model="{model}",provider="{provider}",status_code="{status}"}} {count}'
            )

        lines.append(
            "# HELP crouter_http_requests_in_flight Active in-flight requests"
        )
        lines.append("# TYPE crouter_http_requests_in_flight gauge")
        for tenant_id, count in self.active_in_flight.items():
            lines.append(
                f'crouter_active_in_flight_requests{{tenant_id="{tenant_id}"}} {count}'
            )

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
