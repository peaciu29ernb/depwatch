"""Summarises watch-cycle results for logging and reporting."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.watch_cycle import WatchCycleResult


@dataclass
class WatchSummary:
    total_repos: int
    checked_repos: int
    skipped_repos: int
    total_added: int
    total_modified: int
    total_removed: int

    @property
    def any_changes(self) -> bool:
        return self.total_added > 0 or self.total_modified > 0 or self.total_removed > 0

    def as_text(self) -> str:
        lines = [
            f"Repos total={self.total_repos} checked={self.checked_repos} "
            f"skipped={self.skipped_repos}",
            f"Files added={self.total_added} modified={self.total_modified} "
            f"removed={self.total_removed}",
        ]
        return "\n".join(lines)


def summarise(results: List[WatchCycleResult]) -> WatchSummary:
    """Build a WatchSummary from a list of per-repo WatchCycleResults."""
    checked = sum(1 for r in results if not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    added = sum(len(r.changeset.added) for r in results)
    modified = sum(len(r.changeset.modified) for r in results)
    removed = sum(len(r.changeset.removed) for r in results)
    return WatchSummary(
        total_repos=len(results),
        checked_repos=checked,
        skipped_repos=skipped,
        total_added=added,
        total_modified=modified,
        total_removed=removed,
    )
