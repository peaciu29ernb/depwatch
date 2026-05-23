"""Integrates the watcher into the daemon cycle — only re-checks changed repos."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from depwatch.scanner import ScanResult
from depwatch.watcher import ChangeSet, WatcherState, detect_changes


@dataclass
class WatchCycleResult:
    repo_name: str
    changeset: ChangeSet
    skipped: bool = False


@dataclass
class WatchCycleState:
    """Per-repo watcher states, keyed by repo name."""
    repo_states: Dict[str, WatcherState] = field(default_factory=dict)

    def state_for(self, repo_name: str) -> WatcherState:
        if repo_name not in self.repo_states:
            self.repo_states[repo_name] = WatcherState()
        return self.repo_states[repo_name]


def evaluate_repo(
    repo_name: str,
    scan_result: ScanResult,
    cycle_state: WatchCycleState,
) -> WatchCycleResult:
    """Detect file changes for a single repo's scan result.

    Returns a WatchCycleResult indicating whether anything changed.
    """
    watcher_state = cycle_state.state_for(repo_name)
    changeset = detect_changes(scan_result.dep_files, watcher_state)
    return WatchCycleResult(
        repo_name=repo_name,
        changeset=changeset,
        skipped=not changeset.has_changes,
    )


def evaluate_all_repos(
    scan_results: Dict[str, ScanResult],
    cycle_state: WatchCycleState,
) -> List[WatchCycleResult]:
    """Evaluate all repos, returning results for every repo."""
    results: List[WatchCycleResult] = []
    for repo_name, scan_result in scan_results.items():
        results.append(evaluate_repo(repo_name, scan_result, cycle_state))
    return results
