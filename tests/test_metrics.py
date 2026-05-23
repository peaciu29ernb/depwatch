"""Tests for depwatch.metrics and depwatch.metrics_reporter."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from depwatch.metrics import CycleSample, MetricsStore, make_sample
from depwatch.metrics_reporter import format_metrics_oneline, format_metrics_summary


def _sample(issues: int = 0, errors: int = 0, duration: float = 1.0) -> CycleSample:
    return CycleSample(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        repos_scanned=1,
        total_issues=issues,
        total_errors=errors,
        duration_seconds=duration,
    )


def test_metrics_store_starts_empty():
    store = MetricsStore()
    assert store.total_cycles == 0
    assert store.total_issues_seen == 0
    assert store.total_errors_seen == 0
    assert store.average_duration == 0.0
    assert store.latest() is None


def test_metrics_store_records_samples():
    store = MetricsStore()
    store.record(_sample(issues=3, errors=1, duration=2.0))
    store.record(_sample(issues=5, errors=0, duration=4.0))
    assert store.total_cycles == 2
    assert store.total_issues_seen == 8
    assert store.total_errors_seen == 1


def test_metrics_store_average_duration():
    store = MetricsStore()
    store.record(_sample(duration=2.0))
    store.record(_sample(duration=4.0))
    assert store.average_duration == pytest.approx(3.0)


def test_metrics_store_latest():
    store = MetricsStore()
    s1 = _sample(issues=1)
    s2 = _sample(issues=9)
    store.record(s1)
    store.record(s2)
    assert store.latest() is s2


def test_metrics_store_issue_counts_by_cycle():
    store = MetricsStore()
    store.record(_sample(issues=2))
    store.record(_sample(issues=7))
    assert store.issue_counts_by_cycle == [2, 7]


def test_metrics_store_as_dict_keys():
    store = MetricsStore()
    d = store.as_dict()
    assert "total_cycles" in d
    assert "total_issues_seen" in d
    assert "total_errors_seen" in d
    assert "average_duration_seconds" in d


def test_make_sample_sets_timestamp():
    s = make_sample(repos_scanned=2, total_issues=4, total_errors=0, duration_seconds=1.5)
    assert s.repos_scanned == 2
    assert s.total_issues == 4
    assert s.duration_seconds == 1.5
    assert s.timestamp.tzinfo is not None


def test_format_metrics_oneline():
    store = MetricsStore()
    store.record(_sample(issues=3, errors=1, duration=2.0))
    line = format_metrics_oneline(store)
    assert "cycles=1" in line
    assert "issues=3" in line
    assert "errors=1" in line


def test_format_metrics_summary_contains_header():
    store = MetricsStore()
    store.record(_sample(issues=2, duration=0.5))
    text = format_metrics_summary(store)
    assert "depwatch metrics" in text
    assert "Cycles run" in text
    assert "Issues per cycle" in text


def test_format_metrics_summary_empty_store():
    store = MetricsStore()
    text = format_metrics_summary(store)
    assert "depwatch metrics" in text
    assert "Issues per cycle" not in text
