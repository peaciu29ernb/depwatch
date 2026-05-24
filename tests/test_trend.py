"""Tests for depwatch.trend and depwatch.trend_reporter."""
from __future__ import annotations

import time
from typing import List

import pytest

from depwatch.digest import DigestEntry
from depwatch.trend import TrendPoint, TrendResult, build_trend
from depwatch.trend_reporter import format_trend_oneline, format_trend_summary


def _entry(total_issues: int, total_vulnerable: int = 0, total_outdated: int = 0,
           offset: float = 0.0) -> DigestEntry:
    return DigestEntry(
        timestamp=time.time() + offset,
        total_issues=total_issues,
        total_vulnerable=total_vulnerable,
        total_outdated=total_outdated,
        had_errors=False,
    )


# ---------------------------------------------------------------------------
# build_trend
# ---------------------------------------------------------------------------

def test_build_trend_empty_returns_no_data():
    result = build_trend([])
    assert not result.has_data
    assert result.direction == "stable"


def test_build_trend_single_entry_no_data():
    result = build_trend([_entry(5)])
    assert not result.has_data
    assert len(result.points) == 1


def test_build_trend_rising():
    result = build_trend([_entry(3), _entry(7)])
    assert result.has_data
    assert result.delta_issues == 4
    assert result.direction == "rising"


def test_build_trend_falling():
    result = build_trend([_entry(10), _entry(4)])
    assert result.delta_issues == -6
    assert result.direction == "falling"


def test_build_trend_stable():
    result = build_trend([_entry(5), _entry(5)])
    assert result.delta_issues == 0
    assert result.direction == "stable"


def test_build_trend_vulnerable_delta():
    result = build_trend([_entry(5, total_vulnerable=1), _entry(5, total_vulnerable=3)])
    assert result.delta_vulnerable == 2


def test_build_trend_outdated_delta():
    result = build_trend([_entry(5, total_outdated=2), _entry(5, total_outdated=0)])
    assert result.delta_outdated == -2


def test_build_trend_uses_last_two_for_delta():
    entries = [_entry(1), _entry(2), _entry(10)]
    result = build_trend(entries)
    assert result.delta_issues == 8   # 10 - 2
    assert len(result.points) == 3


# ---------------------------------------------------------------------------
# trend_reporter
# ---------------------------------------------------------------------------

def test_format_trend_oneline_insufficient_data():
    result = TrendResult()
    text = format_trend_oneline(result)
    assert "insufficient" in text


def test_format_trend_oneline_rising():
    result = build_trend([_entry(2), _entry(5)])
    text = format_trend_oneline(result)
    assert "rising" in text
    assert "+3" in text


def test_format_trend_oneline_falling():
    result = build_trend([_entry(8), _entry(3)])
    text = format_trend_oneline(result)
    assert "falling" in text


def test_format_trend_summary_contains_direction():
    result = build_trend([_entry(1), _entry(4)])
    text = format_trend_summary(result)
    assert "rising" in text
    assert "Δ issues" in text


def test_format_trend_summary_no_data():
    result = TrendResult()
    text = format_trend_summary(result)
    assert "Not enough" in text
