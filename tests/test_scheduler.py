"""Tests for depwatch.scheduler."""

from __future__ import annotations

from unittest.mock import call, patch

import pytest

from depwatch.scheduler import (
    SchedulerConfig,
    SchedulerState,
    compute_next_delay,
    run_scheduler,
)


# ---------------------------------------------------------------------------
# SchedulerState
# ---------------------------------------------------------------------------

def test_scheduler_state_defaults():
    state = SchedulerState()
    assert state.consecutive_failures == 0
    assert state.last_run_at is None
    assert state.total_runs == 0


def test_record_success_resets_failures():
    state = SchedulerState()
    state.consecutive_failures = 3
    state.record_success()
    assert state.consecutive_failures == 0
    assert state.total_runs == 1
    assert state.last_success_at is not None


def test_record_failure_increments_counters():
    state = SchedulerState()
    state.record_failure()
    state.record_failure()
    assert state.consecutive_failures == 2
    assert state.total_failures == 2
    assert state.total_runs == 2


def test_backoff_delay_zero_when_no_failures():
    state = SchedulerState()
    cfg = SchedulerConfig(interval_seconds=3600, backoff_factor=2.0, max_backoff_seconds=900)
    assert state.backoff_delay(cfg) == 0.0


def test_backoff_delay_capped_at_max():
    state = SchedulerState()
    state.consecutive_failures = 20  # would be huge without cap
    cfg = SchedulerConfig(interval_seconds=3600, backoff_factor=2.0, max_backoff_seconds=900)
    assert state.backoff_delay(cfg) == 900


def test_backoff_delay_first_failure_equals_interval():
    state = SchedulerState()
    state.consecutive_failures = 1
    cfg = SchedulerConfig(interval_seconds=60, backoff_factor=2.0, max_backoff_seconds=900)
    assert state.backoff_delay(cfg) == 60.0


# ---------------------------------------------------------------------------
# compute_next_delay
# ---------------------------------------------------------------------------

def test_compute_next_delay_no_failure_uses_interval():
    state = SchedulerState()
    cfg = SchedulerConfig(interval_seconds=3600)
    delay = compute_next_delay(state, cfg, jitter_fn=lambda: 0.0)
    assert delay == 3600


def test_compute_next_delay_applies_jitter():
    state = SchedulerState()
    cfg = SchedulerConfig(interval_seconds=3600)
    delay = compute_next_delay(state, cfg, jitter_fn=lambda: 30.0)
    assert delay == 3630


def test_compute_next_delay_uses_backoff_on_failure():
    state = SchedulerState()
    state.consecutive_failures = 1
    cfg = SchedulerConfig(interval_seconds=60, backoff_factor=2.0, max_backoff_seconds=900)
    delay = compute_next_delay(state, cfg, jitter_fn=lambda: 99.0)  # jitter ignored
    assert delay == 60.0


# ---------------------------------------------------------------------------
# run_scheduler
# ---------------------------------------------------------------------------

def test_run_scheduler_runs_exact_cycles():
    calls = []
    def cycle():
        calls.append(1)
        return True

    cfg = SchedulerConfig(interval_seconds=10)
    state = run_scheduler(cycle, cfg, max_cycles=3, sleep_fn=lambda _: None)
    assert len(calls) == 3
    assert state.total_runs == 3


def test_run_scheduler_records_failures():
    def cycle():
        return False

    cfg = SchedulerConfig(interval_seconds=10, max_backoff_seconds=5)
    state = run_scheduler(cycle, cfg, max_cycles=2, sleep_fn=lambda _: None)
    assert state.total_failures == 2
    assert state.last_success_at is None


def test_run_scheduler_sleeps_between_cycles():
    sleep_calls: list[float] = []
    cfg = SchedulerConfig(interval_seconds=120)
    run_scheduler(
        lambda: True,
        cfg,
        max_cycles=3,
        sleep_fn=sleep_calls.append,
        jitter_fn=lambda: 0.0,
    )
    # sleep is called between cycles, so 2 times for 3 cycles
    assert len(sleep_calls) == 2
    assert all(s == 120 for s in sleep_calls)
