"""Summarise an AuditLog into human-readable text or structured stats."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.audit_log import AuditEntry, AuditLog


@dataclass
class AuditSummary:
    total_cycles: int
    total_issues_seen: int
    total_errors: int
    repos: List[str]
    most_recent_timestamp: str

    def as_text(self) -> str:
        repos_str = ", ".join(sorted(set(self.repos))) or "(none)"
        lines = [
            "=== Audit Summary ===",
            f"Cycles recorded : {self.total_cycles}",
            f"Total issues    : {self.total_issues_seen}",
            f"Cycles w/ errors: {self.total_errors}",
            f"Repos seen      : {repos_str}",
            f"Last entry      : {self.most_recent_timestamp}",
        ]
        return "\n".join(lines)


def summarise_log(log: AuditLog) -> AuditSummary:
    """Derive an :class:`AuditSummary` from all entries in *log*."""
    entries: List[AuditEntry] = log.entries()
    if not entries:
        return AuditSummary(
            total_cycles=0,
            total_issues_seen=0,
            total_errors=0,
            repos=[],
            most_recent_timestamp="",
        )
    return AuditSummary(
        total_cycles=len(entries),
        total_issues_seen=sum(e.total_issues for e in entries),
        total_errors=sum(1 for e in entries if e.had_errors),
        repos=[e.repo for e in entries],
        most_recent_timestamp=entries[-1].timestamp,
    )


def top_repos_by_issues(log: AuditLog, n: int = 5) -> List[str]:
    """Return the *n* repo names that accumulated the most issues."""
    totals: dict[str, int] = {}
    for entry in log.entries():
        totals[entry.repo] = totals.get(entry.repo, 0) + entry.total_issues
    ranked = sorted(totals, key=lambda r: totals[r], reverse=True)
    return ranked[:n]
