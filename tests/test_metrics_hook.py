"""Tests for depwatch.metrics_hook."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pytest

from depwatch.metrics_hook import MetricsHook
from depwatch.reporter import Report
from depwatch.checker import CheckResult


def _make_report(n_repos: int = 2, issues: int = 0, errors: int = 0) -> Report:
    check_results: Dict[str, CheckResult] = {
        f"repo{i}": CheckResult(dep_file=None, issues=[])  # type: ignore[arg-type]
        for i in range(n_repos)
    }
    return Report(
        check_results=check_results,
        errors=[f"err{i}" for i in range(errors)],
    )


def test_metrics_hook_records_after_cycle():
    hook = MetricsHook()
    hook.before_cycle()
    report = _make_report(n_repos=3)
    hook.after_cycle(report)
    assert hook.store.total_cycles == 1


def test_metrics_hook_repos_scanned():
    hook = MetricsHook()
    hook.before_cycle()
    hook.after_cycle(_make_report(n_repos=4))
    sample = hook.store.latest()
    assert sample is not None
    assert sample.repos_scanned == 4


def test_metrics_hook_errors_counted():
    hook = MetricsHook()
    hook.before_cycle()
    hook.after_cycle(_make_report(errors=2))
    sample = hook.store.latest()
    assert sample.total_errors == 2


def test_metrics_hook_duration_positive():
    import time
    hook = MetricsHook()
    hook.before_cycle()
    time.sleep(0.01)
    hook.after_cycle(_make_report())
    sample = hook.store.latest()
    assert sample.duration_seconds > 0


def test_metrics_hook_multiple_cycles():
    hook = MetricsHook()
    for _ in range(5):
        hook.before_cycle()
        hook.after_cycle(_make_report())
    assert hook.store.total_cycles == 5


def test_metrics_hook_summary_string():
    hook = MetricsHook()
    hook.before_cycle()
    hook.after_cycle(_make_report())
    s = hook.summary
    assert "cycles=1" in s
