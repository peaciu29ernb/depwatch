"""Hook that builds and exposes a TrendResult after each daemon cycle."""
from __future__ import annotations

from typing import Optional

from depwatch.digest import DigestEntry, DigestHook
from depwatch.reporter import Report
from depwatch.trend import TrendResult, build_trend
from depwatch.trend_reporter import format_trend_oneline


class TrendHook:
    """Wraps a DigestHook and computes trend information after every cycle."""

    def __init__(self, digest_hook: DigestHook) -> None:
        self._digest = digest_hook
        self._trend: Optional[TrendResult] = None

    # ------------------------------------------------------------------
    # Hook interface
    # ------------------------------------------------------------------

    def after_cycle(self, report: Report) -> None:
        """Update the digest then recompute the trend."""
        self._digest.after_cycle(report)
        self._trend = build_trend(list(self._digest.summary().entries))

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def trend(self) -> Optional[TrendResult]:
        return self._trend

    def summary(self) -> str:
        if self._trend is None:
            return "trend: no data"
        return format_trend_oneline(self._trend)
