"""Trend analysis: compare successive digest entries to detect rising/falling issue counts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from depwatch.digest import DigestEntry


@dataclass
class TrendPoint:
    timestamp: float
    total_issues: int
    total_vulnerable: int
    total_outdated: int


@dataclass
class TrendResult:
    points: List[TrendPoint] = field(default_factory=list)
    delta_issues: int = 0          # latest - previous
    delta_vulnerable: int = 0
    delta_outdated: int = 0
    direction: str = "stable"      # "rising", "falling", "stable"

    @property
    def has_data(self) -> bool:
        return len(self.points) >= 2


def _direction(delta: int) -> str:
    if delta > 0:
        return "rising"
    if delta < 0:
        return "falling"
    return "stable"


def build_trend(entries: List[DigestEntry]) -> TrendResult:
    """Build a TrendResult from a chronologically ordered list of DigestEntry objects."""
    if not entries:
        return TrendResult()

    points = [
        TrendPoint(
            timestamp=e.timestamp,
            total_issues=e.total_issues,
            total_vulnerable=e.total_vulnerable,
            total_outdated=e.total_outdated,
        )
        for e in entries
    ]

    if len(points) < 2:
        return TrendResult(points=points)

    latest = points[-1]
    previous = points[-2]

    delta_issues = latest.total_issues - previous.total_issues
    delta_vulnerable = latest.total_vulnerable - previous.total_vulnerable
    delta_outdated = latest.total_outdated - previous.total_outdated

    return TrendResult(
        points=points,
        delta_issues=delta_issues,
        delta_vulnerable=delta_vulnerable,
        delta_outdated=delta_outdated,
        direction=_direction(delta_issues),
    )
