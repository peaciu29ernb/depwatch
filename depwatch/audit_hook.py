"""Hook that writes an AuditEntry after every daemon cycle."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from depwatch.audit_log import AuditLog, make_entry
from depwatch.reporter import Report


class AuditHook:
    """Attaches to the daemon cycle and records outcomes in an :class:`AuditLog`."""

    def __init__(self, log_path: Path, max_entries: int = 500) -> None:
        self._log = AuditLog(path=log_path, max_entries=max_entries)

    # ------------------------------------------------------------------
    def after_cycle(
        self,
        repo: str,
        report: Optional[Report],
        had_errors: bool,
        note: Optional[str] = None,
    ) -> None:
        """Record one cycle outcome.  Safe to call with *report=None*."""
        if report is not None:
            total_issues = report.total_issues
            total_outdated = report.total_outdated
            total_vulnerable = report.total_vulnerable
        else:
            total_issues = 0
            total_outdated = 0
            total_vulnerable = 0

        entry = make_entry(
            repo=repo,
            total_issues=total_issues,
            total_outdated=total_outdated,
            total_vulnerable=total_vulnerable,
            had_errors=had_errors,
            note=note,
        )
        self._log.record(entry)

    # ------------------------------------------------------------------
    @property
    def log(self) -> AuditLog:
        return self._log
