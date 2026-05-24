"""Tests for depwatch.rate_limiter and depwatch.rate_limiter_hook."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from depwatch.rate_limiter import RateLimiter, RateLimiterConfig
from depwatch.rate_limiter_hook import RateLimiterHook


# ---------------------------------------------------------------------------
# RateLimiter unit tests
# ---------------------------------------------------------------------------

def test_rate_limiter_allows_when_tokens_available():
    rl = RateLimiter(RateLimiterConfig(max_tokens=5, initial_tokens=5))
    assert rl.acquire() is True


def test_rate_limiter_denies_when_bucket_empty():
    rl = RateLimiter(RateLimiterConfig(max_tokens=2, initial_tokens=0, refill_rate=0.0))
    assert rl.acquire() is False


def test_rate_limiter_consumes_tokens():
    rl = RateLimiter(RateLimiterConfig(max_tokens=3, initial_tokens=3, refill_rate=0.0))
    rl.acquire()
    rl.acquire()
    assert rl.available < 2.0


def test_rate_limiter_refills_over_time():
    rl = RateLimiter(RateLimiterConfig(max_tokens=10, initial_tokens=0, refill_rate=100.0))
    time.sleep(0.05)  # 5 tokens at 100/s
    assert rl.available >= 1.0


def test_rate_limiter_does_not_exceed_max_tokens():
    rl = RateLimiter(RateLimiterConfig(max_tokens=5, initial_tokens=5, refill_rate=1000.0))
    time.sleep(0.05)
    assert rl.available <= 5.0


def test_rate_limiter_stats_track_allowed_and_denied():
    rl = RateLimiter(RateLimiterConfig(max_tokens=2, initial_tokens=2, refill_rate=0.0))
    rl.acquire()
    rl.acquire()
    rl.acquire()  # denied
    stats = rl.stats
    assert stats["total_allowed"] == 2
    assert stats["total_denied"] == 1


def test_rate_limiter_acquire_multiple_tokens():
    rl = RateLimiter(RateLimiterConfig(max_tokens=10, initial_tokens=10, refill_rate=0.0))
    assert rl.acquire(tokens=5) is True
    assert rl.acquire(tokens=6) is False  # only 5 left


# ---------------------------------------------------------------------------
# RateLimiterHook tests
# ---------------------------------------------------------------------------

def _make_report() -> MagicMock:
    report = MagicMock()
    report.total_issues = 3
    return report


def test_rate_limiter_hook_allows_when_tokens_available():
    hook = RateLimiterHook(RateLimiterConfig(max_tokens=5, initial_tokens=5))
    result = hook.before_notify(_make_report())
    assert result.allowed is True


def test_rate_limiter_hook_denies_when_empty():
    hook = RateLimiterHook(RateLimiterConfig(max_tokens=1, initial_tokens=0, refill_rate=0.0))
    result = hook.before_notify(_make_report())
    assert result.allowed is False
    assert result.denied_count == 1


def test_rate_limiter_hook_summary_contains_key_fields():
    hook = RateLimiterHook(RateLimiterConfig(max_tokens=5, initial_tokens=5))
    hook.before_notify(_make_report())
    summary = hook.summary()
    assert "allowed" in summary
    assert "denied" in summary
    assert "available" in summary
