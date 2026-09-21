import time
import math
import logging
from typing import Optional, Tuple, Dict, Any
from apps.gateway.core.config import settings
from apps.gateway.core.errors import CRouterException

logger = logging.getLogger("crouter.limiter")

SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
local clear_before = now - window

-- Remove expired elements
redis.call('ZREMRANGEBYSCORE', key, '-inf', clear_before)

-- Count remaining elements in window
local current_count = redis.call('ZCARD', key)

if current_count < limit then
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, math.ceil(window) + 5)
    return {1, 0}
else
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 10
    if oldest and #oldest >= 2 then
        local oldest_ts = tonumber(oldest[2])
        retry_after = math.max(1, math.ceil(oldest_ts + window - now))
    end
    return {0, retry_after}
end
"""


class RateLimiter:
    """Sliding-window rate limiter backed by Redis with atomic Lua script and in-memory fallback."""

    def __init__(self, redis_client: Optional[Any] = None):
        self.redis = redis_client
        self._local_buckets: Dict[str, list[float]] = {}
        self._lua_sha: Optional[str] = None

    async def check_rate_limit(
        self, key_id: str, limit_rpm: int
    ) -> Tuple[bool, int]:
        """Check if key has remaining quota within the current 60s sliding window.

        Returns: (allowed: bool, retry_after: int)
        """
        now = time.time()
        window_seconds = 60.0

        if self.redis:
            try:
                zset_key = f"crouter:ratelimit:zset:{key_id}"
                member = f"{now}_{time.perf_counter()}"
                res = await self.redis.eval(
                    SLIDING_WINDOW_LUA,
                    1,
                    zset_key,
                    str(now),
                    str(window_seconds),
                    str(limit_rpm),
                    member,
                )
                allowed = bool(res[0] == 1)
                retry_after = int(res[1])
                return allowed, retry_after
            except Exception as e:
                logger.warning(f"Redis rate limit check error: {e}")
                if not settings.REDIS_FALLBACK_IN_MEMORY:
                    raise CRouterException(
                        f"Redis rate limit error and fallback disabled: {e}",
                        status_code=500,
                        error_code="redis_outage",
                    )
        elif not settings.REDIS_FALLBACK_IN_MEMORY:
            raise CRouterException(
                "Redis connection is required in production mode (REDIS_FALLBACK_IN_MEMORY=False).",
                status_code=500,
                error_code="redis_outage",
            )

        # Local in-memory sliding window
        timestamps = self._local_buckets.setdefault(key_id, [])
        cutoff = now - window_seconds
        # Prune old timestamps
        valid_timestamps = [ts for ts in timestamps if ts > cutoff]
        self._local_buckets[key_id] = valid_timestamps

        if len(valid_timestamps) >= limit_rpm:
            oldest = valid_timestamps[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, retry_after

        valid_timestamps.append(now)
        return True, 0


class ConcurrencyLeaser:
    """In-flight concurrency limiter and connection leaser."""

    def __init__(self, redis_client: Optional[Any] = None, lease_ttl_seconds: int = 60):
        self.redis = redis_client
        self.lease_ttl = lease_ttl_seconds
        self._local_concurrency: Dict[str, int] = {}

    async def acquire(self, key_id: str, max_concurrency: int) -> Tuple[bool, int]:
        """Attempt to acquire a concurrency lease.

        Returns: (acquired: bool, current_active: int)
        """
        redis_key = f"crouter:concurrency:{key_id}"
        if self.redis:
            try:
                current = await self.redis.incr(redis_key)
                await self.redis.expire(redis_key, self.lease_ttl)
                if current > max_concurrency:
                    await self.redis.decr(redis_key)
                    return False, current - 1
                return True, current
            except Exception as e:
                logger.warning(f"Redis concurrency acquire error: {e}")
                if not settings.REDIS_FALLBACK_IN_MEMORY:
                    raise CRouterException(
                        f"Redis concurrency error: {e}",
                        status_code=500,
                        error_code="redis_outage",
                    )
        elif not settings.REDIS_FALLBACK_IN_MEMORY:
            raise CRouterException(
                "Redis connection is required in production mode (REDIS_FALLBACK_IN_MEMORY=False).",
                status_code=500,
                error_code="redis_outage",
            )

        current = self._local_concurrency.get(key_id, 0)
        if current >= max_concurrency:
            return False, current
        self._local_concurrency[key_id] = current + 1
        return True, current + 1

    async def release(self, key_id: str) -> None:
        """Release an acquired concurrency lease."""
        redis_key = f"crouter:concurrency:{key_id}"
        if self.redis:
            try:
                val = await self.redis.decr(redis_key)
                if val < 0:
                    await self.redis.set(redis_key, 0)
                return
            except Exception as e:
                logger.warning(f"Redis concurrency release error: {e}")
                if not settings.REDIS_FALLBACK_IN_MEMORY:
                    raise CRouterException(
                        f"Redis concurrency release error: {e}",
                        status_code=500,
                        error_code="redis_outage",
                    )

        current = self._local_concurrency.get(key_id, 0)
        if current > 0:
            self._local_concurrency[key_id] = current - 1
