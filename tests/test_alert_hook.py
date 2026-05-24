"""Tests for depwatch.alert_hook and depwatch.alert_log."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from depwatch.alert_hook import AlertHook, AlertHookResult
from depwatch.alert_log import AlertLog, AlertLogEntry
from depwatch.alert_policy import AlertPolicy
from depwatch.checker import CheckResult, PackageIssue
from depwatch.reporter import Report
from depwatch.scanner import FoundDepFile


def _dep_file() -> FoundDepFile:
    return FoundDepFile(path="/repo/requirements.txt", ecosystem="pip")


def _issue() -> PackageIssue:
    return PackageIssue(
        package="django",
        current_version="3.0.0",
        latest_version="4.0.0",
        is_outdated=True,
        is_vulnerable=False,
    )


def _report(n_issues: int = 1, repo: str = "repo") -> Report:
    issues = [_issue() for _ in range(n_issues)]
    cr = CheckResult(dep_file=_dep_file(), issues=issues, repo=repo)
    return Report(check_results=[cr])


# ── AlertHook ──────────────────────────────────────────────────────────────

def test_alert_hook_sends_when_policy_met():
    notifier = MagicMock()
    hook = AlertHook(policy=AlertPolicy(min_issues=1), notifiers=[notifier])
    result = hook.after_cycle(_report(n_issues=1))
    assert result.notification_sent is True
    notifier.send.assert_called_once()


def test_alert_hook_suppresses_when_below_threshold():
    notifier = MagicMock()
    hook = AlertHook(policy=AlertPolicy(min_issues=5), notifiers=[notifier])
    result = hook.after_cycle(_report(n_issues=1))
    assert result.notification_sent is False
    notifier.send.assert_not_called()


def test_alert_hook_tracks_totals():
    hook = AlertHook(policy=AlertPolicy(min_issues=1))
    hook.after_cycle(_report(n_issues=2))
    hook.after_cycle(_report(n_issues=0))
    assert hook.total_alerts_sent == 1
    assert hook.total_suppressed == 1


def test_alert_hook_summary_string():
    hook = AlertHook(policy=AlertPolicy(min_issues=1))
    hook.after_cycle(_report(n_issues=1))
    s = hook.summary()
    assert "1 alert" in s


def test_alert_hook_no_notifiers_still_returns_result():
    hook = AlertHook(policy=AlertPolicy(min_issues=1), notifiers=[])
    result = hook.after_cycle(_report(n_issues=1))
    assert isinstance(result, AlertHookResult)
    assert result.decision.should_alert is True
    assert result.notification_sent is False


# ── AlertLog ───────────────────────────────────────────────────────────────

def test_alert_log_creates_file(tmp_path: Path):
    log = AlertLog(tmp_path / "alerts" / "alert.json")
    entry = AlertLogEntry.now(should_alert=True, reason="test", total_issues=3)
    log.append(entry)
    assert (tmp_path / "alerts" / "alert.json").exists()


def test_alert_log_persists_entries(tmp_path: Path):
    path = tmp_path / "alert.json"
    log = AlertLog(path)
    log.append(AlertLogEntry.now(True, "r", 2))
    log.append(AlertLogEntry.now(False, "r", 0))
    log2 = AlertLog(path)
    assert len(log2.entries) == 2


def test_alert_log_counts(tmp_path: Path):
    log = AlertLog(tmp_path / "a.json")
    log.append(AlertLogEntry.now(True, "r", 1))
    log.append(AlertLogEntry.now(True, "r", 2))
    log.append(AlertLogEntry.now(False, "r", 0))
    assert log.total_sent == 2
    assert log.total_suppressed == 1


def test_alert_log_starts_empty(tmp_path: Path):
    log = AlertLog(tmp_path / "a.json")
    assert log.entries == []
    assert log.total_sent == 0
