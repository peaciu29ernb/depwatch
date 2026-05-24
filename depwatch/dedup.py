"""Deduplication of PackageIssues across multiple CheckResults."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from depwatch.checker import CheckResult, PackageIssue


@dataclass
class DedupStats:
    total_seen: int = 0
    total_duplicates: int = 0
    total_unique: int = 0

    @property
    def duplicate_rate(self) -> float:
        if self.total_seen == 0:
            return 0.0
        return self.total_duplicates / self.total_seen


@dataclass
class DedupResult:
    issues: List[PackageIssue] = field(default_factory=list)
    stats: DedupStats = field(default_factory=DedupStats)


def _issue_key(issue: PackageIssue) -> tuple:
    """Return a hashable key that uniquely identifies an issue."""
    return (
        issue.ecosystem,
        issue.package_name,
        issue.current_version,
        issue.is_outdated,
        issue.is_vulnerable,
    )


def dedup_issues(check_results: Sequence[CheckResult]) -> DedupResult:
    """Collect all PackageIssues from *check_results* and remove duplicates.

    Two issues are considered duplicates when they share the same ecosystem,
    package name, current version, and flag combination.  The first occurrence
    is kept; subsequent duplicates are counted in *DedupStats*.
    """
    seen: dict[tuple, PackageIssue] = {}
    total_seen = 0
    total_duplicates = 0

    for result in check_results:
        for issue in result.issues:
            total_seen += 1
            key = _issue_key(issue)
            if key in seen:
                total_duplicates += 1
            else:
                seen[key] = issue

    unique_issues = list(seen.values())
    stats = DedupStats(
        total_seen=total_seen,
        total_duplicates=total_duplicates,
        total_unique=len(unique_issues),
    )
    return DedupResult(issues=unique_issues, stats=stats)
