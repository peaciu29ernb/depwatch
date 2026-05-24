"""Tests for depwatch.digest and depwatch.digest_hook."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from depwatch.digest import (
    DigestEntry,
    DigestSummary,
    DigestWindow,
    build_digest,
    entry_from_report,
)
from depwatch.digest_hook import DigestHook


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(
    hours_ago: float = 0,
    total_issues: int = 0,
    total_vulnerable: int = 0,
    total_outdated: int = 0,
    repos_scanned: int = 1,
    had_errors: bool = False,
) -> DigestEntry:
    ts = datetime(2024, 6, 1, 12, 0, 0) - timedelta(hours=hours_ago)
    return DigestEntry(
        timestamp=ts,
        total_issues=total_issues,
        total_vulnerable=total_vulnerable,
        total_outdated=total_outdated,
        repos_scanned=repos_scanned,
        had_errors=had_errors,
    )


NOW = datetime(2024, 6, 1, 12, 0, 0)


# ---------------------------------------------------------------------------
# DigestWindow
# ---------------------------------------------------------------------------

def test_digest_window_default_hours():
    assert DigestWindow().hours == 24


def test_digest_window_delta():
    assert DigestWindow(hours=6).delta == timedelta(hours=6)


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------

def test_build_digest_includes_entries_in_window():
    entries = [_entry(hours_ago=1), _entry(hours_ago=23)]
    summary = build_digest(entries, DigestWindow(hours=24), now=NOW)
    assert summary.total_cycles == 2


def test_build_digest_excludes_entries_outside_window():
    entries = [_entry(hours_ago=1), _entry(hours_ago=25)]
    summary = build_digest(entries, DigestWindow(hours=24), now=NOW)
    assert summary.total_cycles == 1


def test_build_digest_empty_entries():
    summary = build_digest([], DigestWindow(), now=NOW)
    assert summary.total_cycles == 0
    assert summary.total_issues == 0


# ---------------------------------------------------------------------------
# DigestSummary aggregations
# ---------------------------------------------------------------------------

def test_digest_summary_totals():
    entries = [
        _entry(total_issues=3, total_vulnerable=1, total_outdated=2),
        _entry(total_issues=5, total_vulnerable=2, total_outdated=3),
    ]
    s = DigestSummary(window_hours=24, entries=entries)
    assert s.total_issues == 8
    assert s.total_vulnerable == 3
    assert s.total_outdated == 5


def test_digest_summary_cycles_with_errors():
    entries = [_entry(had_errors=True), _entry(had_errors=False), _entry(had_errors=True)]
    s = DigestSummary(window_hours=24, entries=entries)
    assert s.cycles_with_errors == 2


def test_digest_summary_peak_issues_cycle():
    e1 = _entry(total_issues=2)
    e2 = _entry(total_issues=7)
    e3 = _entry(total_issues=4)
    s = DigestSummary(window_hours=24, entries=[e1, e2, e3])
    assert s.peak_issues_cycle is e2


def test_digest_summary_peak_none_when_empty():
    s = DigestSummary(window_hours=24, entries=[])
    assert s.peak_issues_cycle is None


def test_digest_summary_as_text_contains_key_info():
    entries = [_entry(total_issues=3, total_vulnerable=1, total_outdated=2, had_errors=True)]
    s = DigestSummary(window_hours=12, entries=entries)
    text = s.as_text()
    assert "12h" in text
    assert "1 cycles" in text
    assert "3 issues" in text
    assert "1 error" in text


# ---------------------------------------------------------------------------
# DigestHook
# ---------------------------------------------------------------------------

class _FakeReport:
    """Minimal stand-in for reporter.Report."""
    def __init__(self, issues=0, vuln=0, outdated=0, errors=None, check_results=None):
        self.total_issues = issues
        self.total_vulnerable = vuln
        self.total_outdated = outdated
        self.errors = errors or []
        self.check_results = check_results or []


def test_digest_hook_starts_empty():
    hook = DigestHook()
    assert hook.total_entries == 0


def test_digest_hook_after_cycle_records_entry():
    hook = DigestHook()
    report = _FakeReport(issues=4, vuln=2, outdated=2)
    entry = hook.after_cycle(report, timestamp=NOW)
    assert hook.total_entries == 1
    assert entry.total_issues == 4


def test_digest_hook_summary_respects_window():
    hook = DigestHook(window=DigestWindow(hours=24))
    hook.after_cycle(_FakeReport(issues=1), timestamp=NOW - timedelta(hours=1))
    hook.after_cycle(_FakeReport(issues=2), timestamp=NOW - timedelta(hours=30))
    summary = hook.summary(now=NOW)
    assert summary.total_cycles == 1
    assert summary.total_issues == 1


def test_digest_hook_reset_clears_entries():
    hook = DigestHook()
    hook.after_cycle(_FakeReport(issues=1), timestamp=NOW)
    hook.reset()
    assert hook.total_entries == 0
