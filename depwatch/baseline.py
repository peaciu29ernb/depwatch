"""Baseline snapshot: record a known-good issue set and diff against it."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from depwatch.checker import PackageIssue


def _issue_key(issue: PackageIssue) -> str:
    return f"{issue.ecosystem}:{issue.package_name}:{issue.current_version}"


@dataclass
class BaselineSnapshot:
    keys: Set[str] = field(default_factory=set)

    def contains(self, issue: PackageIssue) -> bool:
        return _issue_key(issue) in self.keys

    def size(self) -> int:
        return len(self.keys)


@dataclass
class BaselineDiff:
    new_issues: List[PackageIssue] = field(default_factory=list)
    resolved_keys: Set[str] = field(default_factory=set)

    @property
    def has_new(self) -> bool:
        return len(self.new_issues) > 0

    @property
    def has_resolved(self) -> bool:
        return len(self.resolved_keys) > 0


def diff_against_baseline(
    baseline: BaselineSnapshot, current: List[PackageIssue]
) -> BaselineDiff:
    """Return issues that are new (not in baseline) and keys that resolved."""
    current_keys: Set[str] = {_issue_key(i) for i in current}
    new_issues = [i for i in current if not baseline.contains(i)]
    resolved_keys = baseline.keys - current_keys
    return BaselineDiff(new_issues=new_issues, resolved_keys=resolved_keys)


def save_baseline(issues: List[PackageIssue], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = [_issue_key(i) for i in issues]
    path.write_text(json.dumps(keys, indent=2))


def load_baseline(path: Path) -> BaselineSnapshot:
    if not path.exists():
        return BaselineSnapshot()
    keys: List[str] = json.loads(path.read_text())
    return BaselineSnapshot(keys=set(keys))
