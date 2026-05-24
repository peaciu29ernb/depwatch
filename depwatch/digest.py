"""Periodic digest: aggregates cycle results into a time-windowed summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from depwatch.reporter import Report


@dataclass
class DigestWindow:
    """Configuration for the digest time window."""
    hours: int = 24

    @property
    def delta(self) -> timedelta:
        return timedelta(hours=self.hours)


@dataclass
class DigestEntry:
    """A single cycle's contribution to the digest."""
    timestamp: datetime
    total_issues: int
    total_vulnerable: int
    total_outdated: int
    repos_scanned: int
    had_errors: bool


@dataclass
class DigestSummary:
    """Aggregated summary over a window of digest entries."""
    window_hours: int
    entries: List[DigestEntry] = field(default_factory=list)

    @property
    def total_cycles(self) -> int:
        return len(self.entries)

    @property
    def total_issues(self) -> int:
        return sum(e.total_issues for e in self.entries)

    @property
    def total_vulnerable(self) -> int:
        return sum(e.total_vulnerable for e in self.entries)

    @property
    def total_outdated(self) -> int:
        return sum(e.total_outdated for e in self.entries)

    @property
    def cycles_with_errors(self) -> int:
        return sum(1 for e in self.entries if e.had_errors)

    @property
    def peak_issues_cycle(self) -> Optional[DigestEntry]:
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.total_issues)

    def as_text(self) -> str:
        lines = [
            f"Digest ({self.window_hours}h): {self.total_cycles} cycles, "
            f"{self.total_issues} issues "
            f"({self.total_vulnerable} vuln / {self.total_outdated} outdated), "
            f"{self.cycles_with_errors} error cycles",
        ]
        if self.peak_issues_cycle:
            p = self.peak_issues_cycle
            lines.append(
                f"  Peak: {p.total_issues} issues at "
                f"{p.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        return "\n".join(lines)


def entry_from_report(report: Report, timestamp: Optional[datetime] = None) -> DigestEntry:
    """Build a DigestEntry from a Report produced by a daemon cycle."""
    ts = timestamp or datetime.utcnow()
    return DigestEntry(
        timestamp=ts,
        total_issues=report.total_issues,
        total_vulnerable=report.total_vulnerable,
        total_outdated=report.total_outdated,
        repos_scanned=len(report.check_results),
        had_errors=bool(report.errors),
    )


def build_digest(
    entries: List[DigestEntry],
    window: DigestWindow,
    now: Optional[datetime] = None,
) -> DigestSummary:
    """Filter entries to the window and return a DigestSummary."""
    cutoff = (now or datetime.utcnow()) - window.delta
    in_window = [e for e in entries if e.timestamp >= cutoff]
    return DigestSummary(window_hours=window.hours, entries=in_window)
