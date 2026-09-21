import time
from typing import Optional, Tuple, Dict, Any
from apps.gateway.core.errors import RateLimitExceededError


class RateLimiter:
    """Sliding-window rate limiter backed by Redis with in-memory fallback."""

    def __init__(self, redis_client: Optional[Any] = None):
        self.redis = redis_client
        self._local_buckets: Dict[str, list[float]] = {}

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
                # Sliding window using Redis sorted set
                zset_key = f"crouter:ratelimit:zset:{key_id}"
                pipe = self.redis.pipeline()
                # Remove timestamps older than now - 60s
                pipe.zremrangebyscore(zset_key, 0, now - window_seconds)
                # Count current elements
                pipe.zcard(zset_key)
                # Add current timestamp
                pipe.zadd(zset_key, {f"{now}_{time.perf_counter()}": now})
                # Set TTL
                pipe.expire(zset_key, int(window_seconds) + 5)
                results = await pipe.execute()
                current_count = results[1]

                if current_count >= limit_rpm:
                    # Over limit - find oldest timestamp in window to calculate retry_after
                    oldest = await self.redis.zrange(zset_key, 0, 0, withscores=True)
                    if oldest:
                        retry_after = max(1, int(oldest[0][1] + window_seconds - now))
                    else:
                        retry_after = 10
                    return False, retry_after

                return True, 0
            except Exception:
                pass  # Fallback to local memory if Redis error

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
            except Exception:
                pass

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
            except Exception:
                pass

        current = self._local_concurrency.get(key_id, 0)
        if current > 0:
            self._local_concurrency[key_id] = current - 1
