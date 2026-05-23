"""Health check module for depwatch daemon.

Provides a lightweight snapshot of daemon health based on scheduler
state, audit log, and recent cycle outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from depwatch.scheduler import SchedulerState
from depwatch.audit_log import AuditLog


@dataclass
class HealthStatus:
    healthy: bool
    consecutive_failures: int
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    total_cycles: int
    total_issues_seen: int
    uptime_seconds: float
    notes: list[str] = field(default_factory=list)

    @property
    def summary_line(self) -> str:
        state = "OK" if self.healthy else "DEGRADED"
        return (
            f"[{state}] cycles={self.total_cycles} "
            f"failures={self.consecutive_failures} "
            f"issues_seen={self.total_issues_seen}"
        )


def check_health(
    scheduler_state: SchedulerState,
    audit_log: AuditLog,
    started_at: datetime,
    max_consecutive_failures: int = 3,
) -> HealthStatus:
    """Build a HealthStatus from current runtime state."""
    now = datetime.now(timezone.utc)
    uptime = (now - started_at).total_seconds()

    entries = audit_log.entries
    total_cycles = len(entries)
    total_issues = sum(e.total_issues for e in entries)

    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    for entry in reversed(entries):
        if entry.success and last_success is None:
            last_success = entry.timestamp
        if not entry.success and last_failure is None:
            last_failure = entry.timestamp
        if last_success and last_failure:
            break

    notes: list[str] = []
    consecutive = scheduler_state.consecutive_failures
    healthy = consecutive < max_consecutive_failures

    if not healthy:
        notes.append(
            f"Consecutive failure threshold reached ({consecutive}/{max_consecutive_failures})"
        )
    if total_cycles == 0:
        notes.append("No cycles completed yet")

    return HealthStatus(
        healthy=healthy,
        consecutive_failures=consecutive,
        last_success=last_success,
        last_failure=last_failure,
        total_cycles=total_cycles,
        total_issues_seen=total_issues,
        uptime_seconds=uptime,
        notes=notes,
    )
