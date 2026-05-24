"""Alert policy: decide whether a report warrants sending a notification."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.reporter import Report


@dataclass
class AlertPolicy:
    """Rules that gate notification delivery."""
    min_issues: int = 1
    min_vulnerable: int = 0
    min_outdated: int = 0
    # Repos whose issues should always trigger an alert regardless of counts.
    always_alert_repos: List[str] = field(default_factory=list)


@dataclass
class AlertDecision:
    should_alert: bool
    reason: str

    def __bool__(self) -> bool:  # pragma: no cover
        return self.should_alert


def evaluate_policy(report: Report, policy: AlertPolicy) -> AlertDecision:
    """Return an AlertDecision for *report* given *policy*."""
    total = report.total_issues
    vulnerable = report.total_vulnerable
    outdated = report.total_outdated

    # Always-alert repos: check if any matching repo has issues.
    if policy.always_alert_repos:
        for check in report.check_results:
            if check.repo in policy.always_alert_repos and check.has_issues:
                return AlertDecision(
                    should_alert=True,
                    reason=f"repo '{check.repo}' is in always_alert_repos",
                )

    if policy.min_vulnerable > 0 and vulnerable >= policy.min_vulnerable:
        return AlertDecision(
            should_alert=True,
            reason=f"vulnerable packages ({vulnerable}) >= threshold ({policy.min_vulnerable})",
        )

    if policy.min_outdated > 0 and outdated >= policy.min_outdated:
        return AlertDecision(
            should_alert=True,
            reason=f"outdated packages ({outdated}) >= threshold ({policy.min_outdated})",
        )

    if total >= policy.min_issues:
        return AlertDecision(
            should_alert=True,
            reason=f"total issues ({total}) >= threshold ({policy.min_issues})",
        )

    return AlertDecision(
        should_alert=False,
        reason=f"total issues ({total}) below all thresholds",
    )
