"""Daemon hook that enforces a global rate limit across notification cycles."""

from __future__ import annotations

from dataclasses import dataclass

from depwatch.rate_limiter import RateLimiter, RateLimiterConfig
from depwatch.reporter import Report


@dataclass
class RateLimiterHookResult:
    allowed: bool
    available_tokens: float
    denied_count: int


class RateLimiterHook:
    """Hook that gates notification dispatch behind a shared RateLimiter.

    Intended to be called *before* the notifier in each daemon cycle so that
    a burst of alerts (e.g. many repos suddenly failing) does not hammer
    downstream services.
    """

    def __init__(self, config: RateLimiterConfig | None = None) -> None:
        self._limiter = RateLimiter(config)

    # ------------------------------------------------------------------
    def before_notify(self, report: Report, tokens: int = 1) -> RateLimiterHookResult:
        """Called before sending a notification for *report*.

        Returns a result indicating whether the notification should proceed.
        The caller is responsible for skipping the notifier when
        ``result.allowed`` is False.
        """
        allowed = self._limiter.acquire(tokens)
        stats = self._limiter.stats
        return RateLimiterHookResult(
            allowed=allowed,
            available_tokens=stats["available"],
            denied_count=stats["total_denied"],
        )

    def summary(self) -> str:
        """Human-readable summary of rate-limiter activity."""
        stats = self._limiter.stats
        return (
            f"rate_limiter | allowed={stats['total_allowed']} "
            f"denied={stats['total_denied']} "
            f"available={stats['available']:.1f}"
        )
