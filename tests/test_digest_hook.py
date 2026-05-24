"""Focused integration-style tests for DigestHook."""
from __future__ import annotations

from datetime import datetime, timedelta

from depwatch.digest import DigestWindow
from depwatch.digest_hook import DigestHook

NOW = datetime(2024, 7, 15, 9, 0, 0)


class _Report:
    def __init__(self, issues=0, vuln=0, outdated=0, errors=None, check_results=None):
        self.total_issues = issues
        self.total_vulnerable = vuln
        self.total_outdated = outdated
        self.errors = errors or []
        self.check_results = check_results or [object()]  # one repo by default


def test_hook_multiple_cycles_accumulate():
    hook = DigestHook(window=DigestWindow(hours=48))
    for i in range(5):
        hook.after_cycle(_Report(issues=i), timestamp=NOW - timedelta(hours=i))
    assert hook.total_entries == 5
    summary = hook.summary(now=NOW)
    assert summary.total_cycles == 5
    assert summary.total_issues == sum(range(5))


def test_hook_had_errors_flag_propagated():
    hook = DigestHook()
    hook.after_cycle(_Report(errors=["oops"]), timestamp=NOW)
    summary = hook.summary(now=NOW)
    assert summary.cycles_with_errors == 1


def test_hook_no_errors_flag_when_clean():
    hook = DigestHook()
    hook.after_cycle(_Report(), timestamp=NOW)
    summary = hook.summary(now=NOW)
    assert summary.cycles_with_errors == 0


def test_hook_repos_scanned_from_check_results():
    hook = DigestHook()
    entry = hook.after_cycle(
        _Report(check_results=[object(), object(), object()]),
        timestamp=NOW,
    )
    assert entry.repos_scanned == 3


def test_hook_summary_as_text_smoke():
    hook = DigestHook(window=DigestWindow(hours=24))
    hook.after_cycle(_Report(issues=2, vuln=1, outdated=1), timestamp=NOW)
    text = hook.summary(now=NOW).as_text()
    assert isinstance(text, str)
    assert len(text) > 0


def test_hook_window_default_is_24h():
    hook = DigestHook()
    assert hook.window.hours == 24


def test_hook_custom_window_applied():
    hook = DigestHook(window=DigestWindow(hours=6))
    hook.after_cycle(_Report(issues=1), timestamp=NOW - timedelta(hours=5))
    hook.after_cycle(_Report(issues=1), timestamp=NOW - timedelta(hours=7))
    summary = hook.summary(now=NOW)
    assert summary.total_cycles == 1
