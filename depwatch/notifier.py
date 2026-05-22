"""Notifier module: sends alerts based on report findings."""

from dataclasses import dataclass, field
from typing import Protocol, List
from depwatch.reporter import Report


class NotifierBackend(Protocol):
    """Protocol for notification backends."""

    def send(self, subject: str, body: str) -> None:
        ...


@dataclass
class ConsoleNotifier:
    """Prints alerts to stdout."""

    prefix: str = "[depwatch]"

    def send(self, subject: str, body: str) -> None:
        print(f"{self.prefix} {subject}")
        if body:
            print(body)


@dataclass
class NotificationResult:
    sent: bool = False
    backend: str = ""
    error: str = ""


@dataclass
class Notifier:
    backends: List[NotifierBackend] = field(default_factory=list)
    min_issues: int = 1

    def notify(self, report: Report) -> List[NotificationResult]:
        """Send notifications for a report if it has enough issues."""
        results: List[NotificationResult] = []

        if report.total_issues < self.min_issues:
            return results

        subject = _build_subject(report)
        body = _build_body(report)

        for backend in self.backends:
            result = NotificationResult(backend=type(backend).__name__)
            try:
                backend.send(subject, body)
                result.sent = True
            except Exception as exc:  # noqa: BLE001
                result.error = str(exc)
            results.append(result)

        return results


def _build_subject(report: Report) -> str:
    total = report.total_issues
    vuln = report.total_vulnerable
    return (
        f"depwatch: {total} issue(s) found "
        f"({vuln} vulnerable) across {len(report.check_results)} repo(s)"
    )


def _build_body(report: Report) -> str:
    lines: List[str] = []
    for cr in report.check_results:
        if not cr.has_issues:
            continue
        lines.append(f"Repo: {cr.repo}")
        for issue in cr.issues:
            flag = "VULNERABLE" if issue.is_vulnerable else "outdated"
            lines.append(
                f"  [{flag}] {issue.package} {issue.current_version} -> {issue.latest_version}"
            )
    return "\n".join(lines)
