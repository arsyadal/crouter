import time
import pytest
from apps.gateway.engine.key_pool import ProviderKeyPool


def test_key_pool_round_robin():
    pool = ProviderKeyPool()
    pool.add_keys("gemini", ["key_1", "key_2", "key_3"])

    # First rotation
    k1 = pool.get_key("gemini", strategy="round-robin")
    k2 = pool.get_key("gemini", strategy="round-robin")
    k3 = pool.get_key("gemini", strategy="round-robin")
    # Second rotation
    k4 = pool.get_key("gemini", strategy="round-robin")

    assert [k1, k2, k3] == ["key_1", "key_2", "key_3"]
    assert k4 == "key_1"


def test_key_pool_delimited_string_loading():
    pool = ProviderKeyPool()
    raw = "key_alpha, key_beta; key_gamma\nkey_delta"
    pool.load_from_env_or_string("commandcode", raw)

    keys = pool.get_keys("commandcode")
    assert keys == ["key_alpha", "key_beta", "key_gamma", "key_delta"]


def test_key_pool_rate_limit_backoff():
    pool = ProviderKeyPool()
    pool.add_keys("gemini", ["active_key_1", "rate_limited_key_2"])

    # Mark key 2 as rate limited (429) for 60 seconds
    pool.record_error("gemini", "rate_limited_key_2", is_rate_limit=True, cooldown_seconds=60.0)

    # Next requests should exclusively pick active_key_1
    for _ in range(5):
        selected = pool.get_key("gemini", strategy="round-robin")
        assert selected == "active_key_1"


def test_key_pool_least_error_strategy():
    pool = ProviderKeyPool()
    pool.add_keys("openrouter", ["clean_key", "errored_key"])

    pool.record_error("openrouter", "errored_key", is_rate_limit=False)

    # Least error strategy should select clean_key
    selected = pool.get_key("openrouter", strategy="least-error")
    assert selected == "clean_key"


def test_key_pool_recovery_on_success():
    pool = ProviderKeyPool()
    pool.add_key("gemini", "test_key")

    pool.record_error("gemini", "test_key", is_rate_limit=True, cooldown_seconds=100.0)
    stats_before = pool.get_stats("gemini")
    assert stats_before[0]["is_available"] is False

    # Record success clears cooldown
    pool.record_success("gemini", "test_key")
    stats_after = pool.get_stats("gemini")
    assert stats_after[0]["is_available"] is True
    assert stats_after[0]["error_count"] == 0
