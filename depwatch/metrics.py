"""Lightweight in-process metrics collector for depwatch daemon cycles."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class CycleSample:
    """A single cycle's worth of measurements."""
    timestamp: datetime
    repos_scanned: int
    total_issues: int
    total_errors: int
    duration_seconds: float


@dataclass
class MetricsStore:
    """Accumulates CycleSamples and exposes aggregate statistics."""
    _samples: List[CycleSample] = field(default_factory=list)

    def record(self, sample: CycleSample) -> None:
        self._samples.append(sample)

    @property
    def total_cycles(self) -> int:
        return len(self._samples)

    @property
    def total_issues_seen(self) -> int:
        return sum(s.total_issues for s in self._samples)

    @property
    def total_errors_seen(self) -> int:
        return sum(s.total_errors for s in self._samples)

    @property
    def average_duration(self) -> float:
        if not self._samples:
            return 0.0
        return sum(s.duration_seconds for s in self._samples) / len(self._samples)

    @property
    def issue_counts_by_cycle(self) -> List[int]:
        return [s.total_issues for s in self._samples]

    def latest(self) -> CycleSample | None:
        return self._samples[-1] if self._samples else None

    def as_dict(self) -> Dict[str, object]:
        return {
            "total_cycles": self.total_cycles,
            "total_issues_seen": self.total_issues_seen,
            "total_errors_seen": self.total_errors_seen,
            "average_duration_seconds": round(self.average_duration, 3),
        }


def make_sample(
    repos_scanned: int,
    total_issues: int,
    total_errors: int,
    duration_seconds: float,
) -> CycleSample:
    """Convenience factory that stamps the sample with the current UTC time."""
    return CycleSample(
        timestamp=datetime.now(tz=timezone.utc),
        repos_scanned=repos_scanned,
        total_issues=total_issues,
        total_errors=total_errors,
        duration_seconds=duration_seconds,
    )
