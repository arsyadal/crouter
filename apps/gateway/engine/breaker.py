import time
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):  # type: ignore
        pass
from typing import Optional, Dict, Any


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Circuit breaker state engine for upstream routes.

    States:
      - CLOSED: normal traffic.
      - OPEN: tripped after threshold consecutive/window failures; fails fast.
      - HALF_OPEN: canary attempt after cooldown window.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        redis_client: Optional[Any] = None,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.redis = redis_client
        self._local_state: Dict[str, Dict[str, Any]] = {}

    async def get_state(self, route_key: str) -> CircuitState:
        now = time.time()
        from apps.gateway.core.telemetry import metrics

        if self.redis:
            try:
                state_raw = await self.redis.get(f"crouter:breaker:{route_key}:state")
                if state_raw is not None:
                    raw_str = (
                        state_raw.decode()
                        if isinstance(state_raw, bytes)
                        else str(state_raw)
                    )
                    if "HALF" in raw_str:
                        state = CircuitState.HALF_OPEN
                    elif "OPEN" in raw_str:
                        state = CircuitState.OPEN
                    else:
                        state = CircuitState.CLOSED
                else:
                    state = CircuitState.CLOSED

                if state == CircuitState.OPEN:
                    opened_at_raw = await self.redis.get(
                        f"crouter:breaker:{route_key}:opened_at"
                    )
                    opened_at = float(opened_at_raw) if opened_at_raw else 0.0
                    if now - opened_at >= self.cooldown_seconds:
                        await self.redis.set(
                            f"crouter:breaker:{route_key}:state", CircuitState.HALF_OPEN.value
                        )
                        metrics.set_circuit_breaker_status(route_key, CircuitState.HALF_OPEN.value)
                        return CircuitState.HALF_OPEN

                metrics.set_circuit_breaker_status(route_key, state.value)
                return state
            except Exception:
                pass  # fallback to memory if redis fails

        rec = self._local_state.get(
            route_key,
            {
                "state": CircuitState.CLOSED,
                "failures": 0,
                "opened_at": 0.0,
            },
        )
        if rec["state"] == CircuitState.OPEN:
            if now - rec["opened_at"] >= self.cooldown_seconds:
                rec["state"] = CircuitState.HALF_OPEN
                metrics.set_circuit_breaker_status(route_key, CircuitState.HALF_OPEN.value)
                return CircuitState.HALF_OPEN
        cs = rec["state"]
        metrics.set_circuit_breaker_status(route_key, cs.value)
        return cs

    async def can_execute(self, route_key: str) -> bool:
        state = await self.get_state(route_key)
        return state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    async def record_success(self, route_key: str) -> None:
        from apps.gateway.core.telemetry import metrics
        metrics.set_circuit_breaker_status(route_key, CircuitState.CLOSED.value)

        if self.redis:
            try:
                await self.redis.set(
                    f"crouter:breaker:{route_key}:state", CircuitState.CLOSED.value
                )
                await self.redis.delete(f"crouter:breaker:{route_key}:failures")
                return
            except Exception:
                pass

        self._local_state[route_key] = {
            "state": CircuitState.CLOSED,
            "failures": 0,
            "opened_at": 0.0,
        }

    async def record_failure(self, route_key: str) -> None:
        now = time.time()
        from apps.gateway.core.telemetry import metrics

        current_state = await self.get_state(route_key)
        # If in HALF_OPEN (canary failed), immediately re-trip to OPEN
        if current_state == CircuitState.HALF_OPEN:
            metrics.set_circuit_breaker_status(route_key, CircuitState.OPEN.value)
            if self.redis:
                try:
                    await self.redis.set(
                        f"crouter:breaker:{route_key}:state", CircuitState.OPEN.value
                    )
                    await self.redis.set(
                        f"crouter:breaker:{route_key}:opened_at", str(now)
                    )
                    return
                except Exception:
                    pass
            rec = self._local_state.setdefault(
                route_key,
                {"state": CircuitState.CLOSED, "failures": 0, "opened_at": 0.0},
            )
            rec["state"] = CircuitState.OPEN
            rec["opened_at"] = now
            return

        if self.redis:
            try:
                fails = await self.redis.incr(f"crouter:breaker:{route_key}:failures")
                await self.redis.expire(f"crouter:breaker:{route_key}:failures", 60)
                if fails >= self.failure_threshold:
                    await self.redis.set(
                        f"crouter:breaker:{route_key}:state", CircuitState.OPEN.value
                    )
                    await self.redis.set(
                        f"crouter:breaker:{route_key}:opened_at", str(now)
                    )
                    metrics.set_circuit_breaker_status(route_key, CircuitState.OPEN.value)
                return
            except Exception:
                pass

        rec = self._local_state.setdefault(
            route_key,
            {
                "state": CircuitState.CLOSED,
                "failures": 0,
                "opened_at": 0.0,
            },
        )
        rec["failures"] += 1
        if rec["failures"] >= self.failure_threshold:
            rec["state"] = CircuitState.OPEN
            rec["opened_at"] = now
            metrics.set_circuit_breaker_status(route_key, CircuitState.OPEN.value)

    async def reset(self, route_key: str) -> None:
        """Explicitly reset a route's circuit breaker to CLOSED."""
        await self.record_success(route_key)

    async def trip(self, route_key: str) -> None:
        """Explicitly trip a route's circuit breaker to OPEN."""
        now = time.time()
        from apps.gateway.core.telemetry import metrics

        metrics.set_circuit_breaker_status(route_key, CircuitState.OPEN.value)
        if self.redis:
            try:
                await self.redis.set(f"crouter:breaker:{route_key}:state", CircuitState.OPEN.value)
                await self.redis.set(f"crouter:breaker:{route_key}:opened_at", str(now))
                return
            except Exception:
                pass

        rec = self._local_state.setdefault(
            route_key,
            {"state": CircuitState.CLOSED, "failures": 0, "opened_at": 0.0},
        )
        rec["state"] = CircuitState.OPEN
        rec["opened_at"] = now

