"""Daemon hook that maintains a per-repo baseline and filters already-known issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from depwatch.baseline import (
    BaselineDiff,
    BaselineSnapshot,
    diff_against_baseline,
    load_baseline,
    save_baseline,
)
from depwatch.checker import PackageIssue
from depwatch.reporter import Report


@dataclass
class BaselineHookResult:
    repo_name: str
    new_issues: List[PackageIssue]
    resolved_count: int
    baseline_size: int


@dataclass
class BaselineHook:
    """Load per-repo baselines, diff incoming reports, optionally promote baseline."""

    baseline_dir: Path
    auto_promote: bool = False
    _results: List[BaselineHookResult] = field(default_factory=list, init=False)

    def _baseline_path(self, repo_name: str) -> Path:
        safe = repo_name.replace("/", "_").replace("\\", "_")
        return self.baseline_dir / f"{safe}.json"

    def after_cycle(self, report: Report) -> List[BaselineHookResult]:
        self._results.clear()
        for check_result in report.check_results:
            repo = check_result.dep_file.repo_name
            path = self._baseline_path(repo)
            snapshot: BaselineSnapshot = load_baseline(path)
            issues: List[PackageIssue] = [
                i for i in check_result.issues
            ]
            diff: BaselineDiff = diff_against_baseline(snapshot, issues)
            if self.auto_promote:
                save_baseline(issues, path)
            result = BaselineHookResult(
                repo_name=repo,
                new_issues=diff.new_issues,
                resolved_count=len(diff.resolved_keys),
                baseline_size=snapshot.size(),
            )
            self._results.append(result)
        return list(self._results)

    def promote(self, repo_name: str, issues: List[PackageIssue]) -> None:
        """Manually promote the current issue set as the new baseline."""
        save_baseline(issues, self._baseline_path(repo_name))

    @property
    def total_new(self) -> int:
        return sum(len(r.new_issues) for r in self._results)

    @property
    def total_resolved(self) -> int:
        return sum(r.resolved_count for r in self._results)

    def summary(self) -> str:
        return (
            f"baseline: {self.total_new} new issue(s), "
            f"{self.total_resolved} resolved across "
            f"{len(self._results)} repo(s)"
        )
