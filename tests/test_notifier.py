"""Tests for depwatch.notifier."""

import pytest
from unittest.mock import MagicMock
from depwatch.notifier import Notifier, ConsoleNotifier, NotificationResult, _build_subject, _build_body
from depwatch.reporter import Report
from depwatch.checker import CheckResult, PackageIssue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_issue(package="requests", current="2.0.0", latest="2.28.0", vuln=False):
    return PackageIssue(
        package=package,
        current_version=current,
        latest_version=latest,
        is_vulnerable=vuln,
        is_outdated=not vuln,
        advisory=None,
    )


def _make_report(issues=None):
    cr = CheckResult(
        repo="myrepo",
        dep_file="requirements.txt",
        ecosystem="pip",
        issues=issues or [],
        error=None,
    )
    return Report(check_results=[cr])


# ---------------------------------------------------------------------------
# ConsoleNotifier
# ---------------------------------------------------------------------------

def test_console_notifier_send(capsys):
    notifier = ConsoleNotifier(prefix="[test]")
    notifier.send("hello", "world")
    captured = capsys.readouterr()
    assert "[test] hello" in captured.out
    assert "world" in captured.out


def test_console_notifier_send_no_body(capsys):
    notifier = ConsoleNotifier()
    notifier.send("subject only", "")
    captured = capsys.readouterr()
    assert "subject only" in captured.out


# ---------------------------------------------------------------------------
# Notifier
# ---------------------------------------------------------------------------

def test_notifier_skips_when_below_min_issues():
    backend = MagicMock()
    notifier = Notifier(backends=[backend], min_issues=1)
    report = _make_report(issues=[])
    results = notifier.notify(report)
    assert results == []
    backend.send.assert_not_called()


def test_notifier_sends_when_issues_present():
    backend = MagicMock()
    notifier = Notifier(backends=[backend], min_issues=1)
    report = _make_report(issues=[_make_issue()])
    results = notifier.notify(report)
    assert len(results) == 1
    assert results[0].sent is True
    backend.send.assert_called_once()


def test_notifier_records_error_on_backend_failure():
    backend = MagicMock()
    backend.send.side_effect = RuntimeError("connection refused")
    notifier = Notifier(backends=[backend], min_issues=1)
    report = _make_report(issues=[_make_issue()])
    results = notifier.notify(report)
    assert results[0].sent is False
    assert "connection refused" in results[0].error


def test_notifier_multiple_backends():
    b1, b2 = MagicMock(), MagicMock()
    notifier = Notifier(backends=[b1, b2], min_issues=1)
    report = _make_report(issues=[_make_issue()])
    results = notifier.notify(report)
    assert len(results) == 2
    b1.send.assert_called_once()
    b2.send.assert_called_once()


# ---------------------------------------------------------------------------
# Subject / body helpers
# ---------------------------------------------------------------------------

def test_build_subject_contains_counts():
    report = _make_report(issues=[_make_issue(vuln=True)])
    subject = _build_subject(report)
    assert "1 issue" in subject
    assert "1 vulnerable" in subject


def test_build_body_marks_vulnerable():
    report = _make_report(issues=[_make_issue(vuln=True)])
    body = _build_body(report)
    assert "VULNERABLE" in body


def test_build_body_marks_outdated():
    report = _make_report(issues=[_make_issue(vuln=False)])
    body = _build_body(report)
    assert "outdated" in body
