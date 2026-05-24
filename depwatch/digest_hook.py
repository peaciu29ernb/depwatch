"""Hook that accumulates DigestEntries after each daemon cycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from depwatch.digest import DigestEntry, DigestSummary, DigestWindow, build_digest, entry_from_report
from depwatch.reporter import Report


@dataclass
class DigestHook:
    """Collects per-cycle entries and can produce a windowed DigestSummary."""
    window: DigestWindow = field(default_factory=DigestWindow)
    _entries: List[DigestEntry] = field(default_factory=list, init=False, repr=False)

    def after_cycle(self, report: Report, timestamp: Optional[datetime] = None) -> DigestEntry:
        """Record a cycle's report; returns the created DigestEntry."""
        entry = entry_from_report(report, timestamp=timestamp)
        self._entries.append(entry)
        return entry

    def summary(self, now: Optional[datetime] = None) -> DigestSummary:
        """Return a DigestSummary for the configured window."""
        return build_digest(self._entries, self.window, now=now)

    @property
    def total_entries(self) -> int:
        return len(self._entries)

    def reset(self) -> None:
        """Clear all accumulated entries."""
        self._entries.clear()
