"""Tests for depwatch.baseline and depwatch.baseline_hook."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from depwatch.baseline import (
    BaselineSnapshot,
    diff_against_baseline,
    load_baseline,
    save_baseline,
)
from depwatch.baseline_hook import BaselineHook
from depwatch.checker import PackageIssue
from depwatch.scanner import FoundDepFile


def _issue(name: str, version: str = "1.0.0", eco: str = "pip") -> PackageIssue:
    return PackageIssue(
        package_name=name,
        current_version=version,
        latest_version="2.0.0",
        ecosystem=eco,
        is_outdated=True,
        is_vulnerable=False,
        cve_ids=[],
    )


def _dep_file(repo: str = "myrepo") -> FoundDepFile:
    return FoundDepFile(path=Path(f"/repos/{repo}/requirements.txt"), repo_name=repo)


# --- BaselineSnapshot ---

def test_snapshot_contains_known_issue():
    issue = _issue("requests")
    snap = BaselineSnapshot(keys={"pip:requests:1.0.0"})
    assert snap.contains(issue)


def test_snapshot_does_not_contain_unknown():
    snap = BaselineSnapshot(keys={"pip:flask:1.0.0"})
    assert not snap.contains(_issue("requests"))


def test_snapshot_size():
    snap = BaselineSnapshot(keys={"a", "b", "c"})
    assert snap.size() == 3


# --- diff_against_baseline ---

def test_diff_new_issue_detected():
    baseline = BaselineSnapshot(keys=set())
    diff = diff_against_baseline(baseline, [_issue("requests")])
    assert len(diff.new_issues) == 1
    assert diff.has_new


def test_diff_known_issue_not_new():
    baseline = BaselineSnapshot(keys={"pip:requests:1.0.0"})
    diff = diff_against_baseline(baseline, [_issue("requests")])
    assert diff.new_issues == []
    assert not diff.has_new


def test_diff_resolved_issue_detected():
    baseline = BaselineSnapshot(keys={"pip:requests:1.0.0"})
    diff = diff_against_baseline(baseline, [])
    assert "pip:requests:1.0.0" in diff.resolved_keys
    assert diff.has_resolved


# --- save / load baseline ---

def test_save_and_load_roundtrip(tmp_path: Path):
    issues = [_issue("flask"), _issue("django", "2.0.0")]
    path = tmp_path / "baselines" / "repo.json"
    save_baseline(issues, path)
    snap = load_baseline(path)
    assert snap.contains(_issue("flask"))
    assert snap.contains(_issue("django", "2.0.0"))


def test_load_baseline_missing_file_returns_empty(tmp_path: Path):
    snap = load_baseline(tmp_path / "nonexistent.json")
    assert snap.size() == 0


# --- BaselineHook ---

def _make_report(repo: str, issues: list) -> MagicMock:
    cr = MagicMock()
    cr.dep_file = _dep_file(repo)
    cr.issues = issues
    report = MagicMock()
    report.check_results = [cr]
    return report


def test_baseline_hook_all_new_on_empty_baseline(tmp_path: Path):
    hook = BaselineHook(baseline_dir=tmp_path)
    report = _make_report("repo1", [_issue("requests"), _issue("flask")])
    results = hook.after_cycle(report)
    assert len(results) == 1
    assert len(results[0].new_issues) == 2
    assert results[0].baseline_size == 0


def test_baseline_hook_auto_promote_saves_baseline(tmp_path: Path):
    hook = BaselineHook(baseline_dir=tmp_path, auto_promote=True)
    report = _make_report("repo1", [_issue("requests")])
    hook.after_cycle(report)
    saved = load_baseline(tmp_path / "repo1.json")
    assert saved.contains(_issue("requests"))


def test_baseline_hook_summary_string(tmp_path: Path):
    hook = BaselineHook(baseline_dir=tmp_path)
    report = _make_report("repo1", [_issue("requests")])
    hook.after_cycle(report)
    s = hook.summary()
    assert "new" in s
    assert "resolved" in s


def test_baseline_hook_promote_manual(tmp_path: Path):
    hook = BaselineHook(baseline_dir=tmp_path)
    hook.promote("myrepo", [_issue("django")])
    snap = load_baseline(tmp_path / "myrepo.json")
    assert snap.contains(_issue("django"))
