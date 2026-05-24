"""Persistent log of alert decisions made during daemon operation."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List


@dataclass
class AlertLogEntry:
    timestamp: str
    should_alert: bool
    reason: str
    total_issues: int

    @staticmethod
    def now(should_alert: bool, reason: str, total_issues: int) -> "AlertLogEntry":
        return AlertLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            should_alert=should_alert,
            reason=reason,
            total_issues=total_issues,
        )


class AlertLog:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[AlertLogEntry] = self._load()

    # ------------------------------------------------------------------
    def _load(self) -> List[AlertLogEntry]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text())
            return [AlertLogEntry(**r) for r in raw]
        except (json.JSONDecodeError, TypeError):
            return []

    def _save(self) -> None:
        self._path.write_text(json.dumps([asdict(e) for e in self._entries], indent=2))

    # ------------------------------------------------------------------
    def append(self, entry: AlertLogEntry) -> None:
        self._entries.append(entry)
        self._save()

    @property
    def entries(self) -> List[AlertLogEntry]:
        return list(self._entries)

    @property
    def total_sent(self) -> int:
        return sum(1 for e in self._entries if e.should_alert)

    @property
    def total_suppressed(self) -> int:
        return sum(1 for e in self._entries if not e.should_alert)
