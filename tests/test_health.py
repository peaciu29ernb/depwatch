"""Tests for depwatch.health."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from depwatch.scheduler import SchedulerState
from depwatch.audit_log import AuditLog, AuditEntry
from depwatch.health import check_health, HealthStatus


_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_STARTED = _NOW - timedelta(hours=1)


@pytest.fixture
def empty_log(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path / "audit.json")


def _entry(success: bool, issues: int = 0, ts: datetime = _NOW) -> AuditEntry:
    return AuditEntry(
        timestamp=ts,
        repo="repo",
        success=success,
        total_issues=issues,
        errors=[],
    )


def test_health_status_healthy_when_no_failures(empty_log: AuditLog) -> None:
    state = SchedulerState()
    status = check_health(state, empty_log, _STARTED)
    assert status.healthy is True


def test_health_status_degraded_on_threshold(empty_log: AuditLog) -> None:
    state = SchedulerState(consecutive_failures=3)
    status = check_health(state, empty_log, _STARTED, max_consecutive_failures=3)
    assert status.healthy is False


def test_health_consecutive_failures_reflected(empty_log: AuditLog) -> None:
    state = SchedulerState(consecutive_failures=2)
    status = check_health(state, empty_log, _STARTED)
    assert status.consecutive_failures == 2


def test_health_uptime_positive(empty_log: AuditLog) -> None:
    state = SchedulerState()
    status = check_health(state, empty_log, _STARTED)
    assert status.uptime_seconds > 0


def test_health_total_cycles_empty(empty_log: AuditLog) -> None:
    state = SchedulerState()
    status = check_health(state, empty_log, _STARTED)
    assert status.total_cycles == 0


def test_health_total_cycles_with_entries(empty_log: AuditLog) -> None:
    empty_log.append(_entry(True, issues=3))
    empty_log.append(_entry(False, issues=0))
    state = SchedulerState()
    status = check_health(state, empty_log, _STARTED)
    assert status.total_cycles == 2


def test_health_total_issues_aggregated(empty_log: AuditLog) -> None:
    empty_log.append(_entry(True, issues=4))
    empty_log.append(_entry(True, issues=7))
    state = SchedulerState()
    status = check_health(state, empty_log, _STARTED)
    assert status.total_issues_seen == 11


def test_health_last_success_and_failure(empty_log: AuditLog) -> None:
    t1 = _NOW - timedelta(minutes=10)
    t2 = _NOW - timedelta(minutes=5)
    empty_log.append(_entry(True, ts=t1))
    empty_log.append(_entry(False, ts=t2))
    state = SchedulerState()
    status = check_health(state, empty_log, _STARTED)
    assert status.last_success == t1
    assert status.last_failure == t2


def test_health_notes_on_degraded(empty_log: AuditLog) -> None:
    state = SchedulerState(consecutive_failures=5)
    status = check_health(state, empty_log, _STARTED, max_consecutive_failures=3)
    assert any("threshold" in n.lower() for n in status.notes)


def test_summary_line_ok(empty_log: AuditLog) -> None:
    state = SchedulerState()
    status = check_health(state, empty_log, _STARTED)
    assert status.summary_line.startswith("[OK]")


def test_summary_line_degraded(empty_log: AuditLog) -> None:
    state = SchedulerState(consecutive_failures=4)
    status = check_health(state, empty_log, _STARTED, max_consecutive_failures=3)
    assert status.summary_line.startswith("[DEGRADED]")
