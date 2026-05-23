"""Hook that records a CycleSample into a MetricsStore after every daemon cycle."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from depwatch.metrics import MetricsStore, make_sample
from depwatch.reporter import Report


@dataclass
class MetricsHook:
    """Attach to the daemon cycle loop to collect runtime metrics."""
    store: MetricsStore = field(default_factory=MetricsStore)
    _cycle_start: float = field(default=0.0, init=False, repr=False)

    def before_cycle(self) -> None:
        """Call this at the start of each daemon cycle."""
        self._cycle_start = time.monotonic()

    def after_cycle(self, report: Report) -> None:
        """Call this at the end of each daemon cycle with the produced Report."""
        duration = time.monotonic() - self._cycle_start
        sample = make_sample(
            repos_scanned=len(report.check_results),
            total_issues=report.total_issues,
            total_errors=len(report.errors),
            duration_seconds=round(duration, 4),
        )
        self.store.record(sample)

    @property
    def summary(self) -> str:
        from depwatch.metrics_reporter import format_metrics_oneline
        return format_metrics_oneline(self.store)
