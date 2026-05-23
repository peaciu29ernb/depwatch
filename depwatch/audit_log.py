"""Audit log: persists a rolling record of cycle outcomes to disk."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    repo: str
    total_issues: int
    total_outdated: int
    total_vulnerable: int
    had_errors: bool
    note: Optional[str] = None


@dataclass
class AuditLog:
    path: Path
    max_entries: int = 500
    _entries: List[AuditEntry] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        try:
            raw = json.loads(self.path.read_text())
            self._entries = [AuditEntry(**r) for r in raw]
        except Exception:
            self._entries = []

    def _save(self) -> None:
        self._entries = self._entries[-self.max_entries :]
        self.path.write_text(json.dumps([asdict(e) for e in self._entries], indent=2))

    # ------------------------------------------------------------------
    def record(self, entry: AuditEntry) -> None:
        """Append *entry* and flush to disk."""
        self._entries.append(entry)
        self._save()

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def last(self, n: int = 10) -> List[AuditEntry]:
        return self._entries[-n:]


def make_entry(
    repo: str,
    total_issues: int,
    total_outdated: int,
    total_vulnerable: int,
    had_errors: bool,
    note: Optional[str] = None,
) -> AuditEntry:
    """Convenience factory that stamps the current UTC time."""
    ts = datetime.now(timezone.utc).isoformat()
    return AuditEntry(
        timestamp=ts,
        repo=repo,
        total_issues=total_issues,
        total_outdated=total_outdated,
        total_vulnerable=total_vulnerable,
        had_errors=had_errors,
        note=note,
    )
