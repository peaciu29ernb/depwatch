"""Simple token-bucket rate limiter for outbound API calls (e.g. notifiers, checkers)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RateLimiterConfig:
    """Configuration for the token-bucket rate limiter."""

    max_tokens: int = 10          # bucket capacity
    refill_rate: float = 1.0      # tokens added per second
    initial_tokens: int | None = None  # defaults to max_tokens


@dataclass
class RateLimiterState:
    """Mutable runtime state for a single rate limiter instance."""

    tokens: float
    last_refill: float = field(default_factory=time.monotonic)
    total_allowed: int = 0
    total_denied: int = 0


class RateLimiter:
    """Thread-safe token-bucket rate limiter."""

    def __init__(self, config: RateLimiterConfig | None = None) -> None:
        self._cfg = config or RateLimiterConfig()
        initial = (
            self._cfg.initial_tokens
            if self._cfg.initial_tokens is not None
            else self._cfg.max_tokens
        )
        self._state = RateLimiterState(tokens=float(initial))
        self._lock = Lock()

    # ------------------------------------------------------------------
    def _refill(self) -> None:
        """Add tokens based on elapsed time (call with lock held)."""
        now = time.monotonic()
        elapsed = now - self._state.last_refill
        gained = elapsed * self._cfg.refill_rate
        self._state.tokens = min(
            self._cfg.max_tokens,
            self._state.tokens + gained,
        )
        self._state.last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        """Try to consume *tokens* from the bucket.

        Returns True if the request is allowed, False if rate-limited.
        """
        with self._lock:
            self._refill()
            if self._state.tokens >= tokens:
                self._state.tokens -= tokens
                self._state.total_allowed += 1
                return True
            self._state.total_denied += 1
            return False

    @property
    def available(self) -> float:
        """Current token count (approximate, without consuming)."""
        with self._lock:
            self._refill()
            return self._state.tokens

    @property
    def stats(self) -> dict[str, int | float]:
        """Return a snapshot of counters for observability."""
        with self._lock:
            return {
                "available": round(self._state.tokens, 3),
                "total_allowed": self._state.total_allowed,
                "total_denied": self._state.total_denied,
            }
