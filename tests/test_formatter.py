"""Tests for depwatch.formatter."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from depwatch.checker import PackageIssue, CheckResult
from depwatch.reporter import Report
from depwatch.formatter import (
    format_issue,
    format_report,
    FormattedReport,
    SEVERITY_ICONS,
)


def _make_issue(
    name="requests",
    current="2.0.0",
    latest=None,
    outdated=False,
    vulnerable=False,
    severity=None,
):
    return PackageIssue(
        package_name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
        is_vulnerable=vulnerable,
        severity=severity,
        advisory=None,
    )


def _make_report(results=None, ts=None):
    ts = ts or datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    report = MagicMock(spec=Report)
    report.generated_at = ts
    report.results = results or []
    report.total_issues = sum(len(r.issues) for r in report.results)
    report.total_vulnerable = 0
    report.total_outdated = 0
    return report


def test_format_issue_outdated():
    issue = _make_issue(outdated=True, latest="3.0.0")
    text = format_issue(issue)
    assert "requests" in text
    assert "outdated" in text
    assert "3.0.0" in text


def test_format_issue_vulnerable():
    issue = _make_issue(vulnerable=True, severity="high")
    text = format_issue(issue)
    assert "vulnerable" in text
    assert "high" in text
    assert SEVERITY_ICONS["high"] in text


def test_format_issue_both_flags():
    issue = _make_issue(outdated=True, latest="4.0.0", vulnerable=True, severity="critical")
    text = format_issue(issue)
    assert "outdated" in text
    assert "vulnerable" in text


def test_format_issue_no_flags():
    issue = _make_issue()
    text = format_issue(issue)
    assert "requests" in text
    assert "outdated" not in text
    assert "vulnerable" not in text


def test_format_report_returns_formatted_report():
    report = _make_report()
    result = format_report(report)
    assert isinstance(result, FormattedReport)


def test_format_report_title_contains_date():
    report = _make_report()
    result = format_report(report)
    assert "2024-06-01" in result.title


def test_format_report_summary_line():
    report = _make_report()
    report.total_issues = 3
    report.total_vulnerable = 1
    report.total_outdated = 2
    result = format_report(report)
    assert "3 issue(s)" in result.summary_line
    assert "1 vulnerable" in result.summary_line
    assert "2 outdated" in result.summary_line


def test_format_report_max_issues_truncates():
    issue = _make_issue(outdated=True)
    cr = MagicMock(spec=CheckResult)
    cr.has_issues = True
    cr.repo = "myrepo"
    cr.dep_file = "requirements.txt"
    cr.issues = [issue, issue, issue]
    report = _make_report(results=[cr])
    result = format_report(report, max_issues=1)
    assert "2 more" in result.body


def test_full_text_combines_sections():
    report = _make_report()
    result = format_report(report)
    full = result.full_text()
    assert result.title in full
    assert result.summary_line in full
