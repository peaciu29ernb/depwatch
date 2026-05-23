"""Scheduler for periodic depwatch cycles with jitter and backoff."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    interval_seconds: int = 3600  # default: every hour
    jitter_seconds: int = 60      # random jitter to spread load
    max_backoff_seconds: int = 900 # 15 minutes max backoff on failure
    backoff_factor: float = 2.0


@dataclass
class SchedulerState:
    consecutive_failures: int = 0
    last_run_at: Optional[float] = None
    last_success_at: Optional[float] = None
    total_runs: int = 0
    total_failures: int = 0
    _next_run_at: float = field(default_factory=time.monotonic)

    def record_success(self) -> None:
        now = time.monotonic()
        self.last_run_at = now
        self.last_success_at = now
        self.total_runs += 1
        self.consecutive_failures = 0

    def record_failure(self) -> None:
        now = time.monotonic()
        self.last_run_at = now
        self.total_runs += 1
        self.total_failures += 1
        self.consecutive_failures += 1

    def backoff_delay(self, cfg: SchedulerConfig) -> float:
        if self.consecutive_failures == 0:
            return 0.0
        delay = cfg.interval_seconds * (cfg.backoff_factor ** (self.consecutive_failures - 1))
        return min(delay, cfg.max_backoff_seconds)


def compute_next_delay(
    state: SchedulerState,
    cfg: SchedulerConfig,
    *,
    jitter_fn: Callable[[], float] = lambda: 0.0,
) -> float:
    """Return seconds to wait before the next cycle."""
    if state.consecutive_failures > 0:
        delay = state.backoff_delay(cfg)
        logger.warning(
            "Backoff after %d consecutive failure(s): waiting %.0fs",
            state.consecutive_failures,
            delay,
        )
        return delay
    return max(0.0, cfg.interval_seconds + jitter_fn())


def run_scheduler(
    cycle_fn: Callable[[], bool],
    cfg: SchedulerConfig,
    *,
    max_cycles: Optional[int] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    jitter_fn: Callable[[], float] = lambda: 0.0,
) -> SchedulerState:
    """Drive repeated cycles; returns final state."""
    state = SchedulerState()
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        logger.info("Scheduler: starting cycle %d", cycles + 1)
        success = cycle_fn()
        if success:
            state.record_success()
        else:
            state.record_failure()
        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            break
        delay = compute_next_delay(state, cfg, jitter_fn=jitter_fn)
        logger.info("Scheduler: sleeping %.0fs until next cycle", delay)
        sleep_fn(delay)
    return state
