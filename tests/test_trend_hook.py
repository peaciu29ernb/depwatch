"""Tests for depwatch.trend_hook.TrendHook."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from unittest.mock import MagicMock

import pytest

from depwatch.digest import DigestEntry, DigestHook
from depwatch.reporter import Report
from depwatch.trend_hook import TrendHook


# ---------------------------------------------------------------------------
# Minimal Report stub
# ---------------------------------------------------------------------------

def _report(total_issues: int = 0, total_vulnerable: int = 0,
            total_outdated: int = 0, errors: int = 0) -> Report:
    r = MagicMock(spec=Report)
    r.total_issues = total_issues
    r.total_vulnerable = total_vulnerable
    r.total_outdated = total_outdated
    r.errors = [MagicMock()] * errors
    return r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_trend_hook_no_trend_before_cycle():
    hook = TrendHook(DigestHook())
    assert hook.trend is None


def test_trend_hook_trend_none_after_one_cycle():
    hook = TrendHook(DigestHook())
    hook.after_cycle(_report(total_issues=3))
    # Only one data point — not enough for a trend delta
    assert hook.trend is not None
    assert not hook.trend.has_data


def test_trend_hook_has_data_after_two_cycles():
    hook = TrendHook(DigestHook())
    hook.after_cycle(_report(total_issues=2))
    hook.after_cycle(_report(total_issues=5))
    assert hook.trend is not None
    assert hook.trend.has_data
    assert hook.trend.delta_issues == 3


def test_trend_hook_direction_rising():
    hook = TrendHook(DigestHook())
    hook.after_cycle(_report(total_issues=1))
    hook.after_cycle(_report(total_issues=4))
    assert hook.trend.direction == "rising"


def test_trend_hook_direction_falling():
    hook = TrendHook(DigestHook())
    hook.after_cycle(_report(total_issues=10))
    hook.after_cycle(_report(total_issues=3))
    assert hook.trend.direction == "falling"


def test_trend_hook_summary_no_data():
    hook = TrendHook(DigestHook())
    assert "no data" in hook.summary()


def test_trend_hook_summary_after_cycles():
    hook = TrendHook(DigestHook())
    hook.after_cycle(_report(total_issues=2))
    hook.after_cycle(_report(total_issues=6))
    summary = hook.summary()
    assert "rising" in summary
