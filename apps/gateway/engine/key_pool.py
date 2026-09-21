import os
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger("crouter.key_pool")


@dataclass
class KeyEntry:
    key: str
    provider: str
    error_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    backoff_until: float = 0.0
    last_used: float = 0.0

    @property
    def is_available(self) -> bool:
        """A key is available if its rate limit backoff has expired."""
        return time.time() >= self.backoff_until


class ProviderKeyPool:
    """Multi-account round-robin and least-error provider API key pool.

    Supports pooling multiple keys for providers (Gemini, CommandCode, OpenRouter, etc.)
    with automatic rate limit backoff and transparent rotation.
    """

    def __init__(self):
        self._pools: Dict[str, List[KeyEntry]] = {}
        self._rr_indices: Dict[str, int] = {}

    def add_key(self, provider: str, key: str) -> None:
        """Add a single key to the pool for a provider."""
        key = key.strip()
        if not key:
            return
        p_lower = provider.lower()
        if p_lower not in self._pools:
            self._pools[p_lower] = []
            self._rr_indices[p_lower] = 0

        # Avoid duplicates
        for existing in self._pools[p_lower]:
            if existing.key == key:
                return

        self._pools[p_lower].append(KeyEntry(key=key, provider=p_lower))

    def add_keys(self, provider: str, keys: List[str]) -> None:
        """Add multiple keys to the pool."""
        for k in keys:
            self.add_key(provider, k)

    def load_from_env_or_string(self, provider: str, raw: Optional[str]) -> None:
        """Parse comma-, semicolon-, or newline-delimited keys and add them."""
        if not raw:
            return
        # Split by comma, semicolon, or newline
        delimiters = [",", ";", "\n"]
        parts = [raw]
        for d in delimiters:
            next_parts = []
            for p in parts:
                next_parts.extend(p.split(d))
            parts = next_parts

        for part in parts:
            clean = part.strip()
            if clean:
                self.add_key(provider, clean)

    def get_key(self, provider: str, strategy: str = "round-robin") -> Optional[str]:
        """Get the next eligible key for a provider using round-robin or least-error distribution."""
        p_lower = provider.lower()
        pool = self._pools.get(p_lower)
        if not pool:
            return None

        # Filter available keys (not backed off)
        available = [e for e in pool if e.is_available]

        # If all keys are currently backed off, fallback to key closest to cooldown expiry
        if not available:
            logger.warning(f"All keys for provider '{provider}' are backed off. Falling back to earliest recovery.")
            target = min(pool, key=lambda e: e.backoff_until)
            target.last_used = time.time()
            target.total_requests += 1
            return target.key

        if strategy == "least-error":
            target = min(available, key=lambda e: (e.error_count, e.last_used))
        else:
            # Round-robin
            idx = self._rr_indices.get(p_lower, 0) % len(available)
            target = available[idx]
            self._rr_indices[p_lower] = (idx + 1) % len(available)

        target.last_used = time.time()
        target.total_requests += 1
        return target.key

    def record_success(self, provider: str, key: str) -> None:
        """Record successful invocation for a key, decrementing error count."""
        p_lower = provider.lower()
        pool = self._pools.get(p_lower, [])
        for entry in pool:
            if entry.key == key:
                entry.success_count += 1
                entry.error_count = max(0, entry.error_count - 1)
                entry.backoff_until = 0.0
                return

    def record_error(
        self,
        provider: str,
        key: str,
        is_rate_limit: bool = False,
        cooldown_seconds: float = 30.0,
    ) -> None:
        """Record an error for a key, applying cooldown backoff if rate limited."""
        p_lower = provider.lower()
        pool = self._pools.get(p_lower, [])
        for entry in pool:
            if entry.key == key:
                entry.error_count += 1
                if is_rate_limit:
                    entry.backoff_until = time.time() + cooldown_seconds
                    logger.warning(
                        f"Key for provider '{provider}' marked backed-off until +{cooldown_seconds:.1f}s due to 429 rate limit."
                    )
                return

    def get_keys(self, provider: str) -> List[str]:
        """Return all raw keys for a provider."""
        pool = self._pools.get(provider.lower(), [])
        return [e.key for e in pool]

    def get_stats(self, provider: str) -> List[Dict[str, Any]]:
        """Return operational stats for keys of a provider."""
        pool = self._pools.get(provider.lower(), [])
        now = time.time()
        return [
            {
                "key_preview": f"{e.key[:6]}...{e.key[-4:]}" if len(e.key) > 10 else "***",
                "is_available": e.is_available,
                "cooldown_remaining_s": max(0.0, e.backoff_until - now),
                "error_count": e.error_count,
                "success_count": e.success_count,
                "total_requests": e.total_requests,
            }
            for e in pool
        ]


# Singleton KeyPool instance
key_pool = ProviderKeyPool()
