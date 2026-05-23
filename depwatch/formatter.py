"""Formatting utilities for depwatch reports and issues."""
from dataclasses import dataclass
from typing import Optional
from depwatch.reporter import Report
from depwatch.checker import PackageIssue


SEVERITY_ICONS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
    "unknown": "⚪",
}


@dataclass
class FormattedReport:
    title: str
    body: str
    summary_line: str

    def full_text(self) -> str:
        parts = [self.title]
        if self.body:
            parts.append(self.body)
        parts.append(self.summary_line)
        return "\n".join(parts)


def format_issue(issue: PackageIssue) -> str:
    """Return a single-line human-readable description of a package issue."""
    parts = [f"  - {issue.package_name}"]
    if issue.current_version:
        parts.append(f"v{issue.current_version}")
    flags = []
    if issue.is_outdated:
        latest = f" (latest: {issue.latest_version})" if issue.latest_version else ""
        flags.append(f"outdated{latest}")
    if issue.is_vulnerable:
        icon = SEVERITY_ICONS.get((issue.severity or "unknown").lower(), "⚪")
        flags.append(f"{icon} vulnerable [{issue.severity or 'unknown'}]")
    if flags:
        parts.append("—")
        parts.append(", ".join(flags))
    return " ".join(parts)


def format_report(report: Report, max_issues: Optional[int] = None) -> FormattedReport:
    """Convert a Report into a FormattedReport with title, body, and summary."""
    title = f"depwatch report — {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}"

    lines = []
    for check_result in report.results:
        if not check_result.has_issues:
            continue
        lines.append(f"\n[{check_result.repo}] {check_result.dep_file}")
        issues = check_result.issues
        if max_issues is not None:
            issues = issues[:max_issues]
        for issue in issues:
            lines.append(format_issue(issue))
        remaining = len(check_result.issues) - len(issues)
        if remaining > 0:
            lines.append(f"  ... and {remaining} more issue(s)")

    body = "\n".join(lines).strip()

    summary_line = (
        f"Total: {report.total_issues} issue(s) "
        f"({report.total_vulnerable} vulnerable, {report.total_outdated} outdated) "
        f"across {len(report.results)} dep file(s)"
    )

    return FormattedReport(title=title, body=body, summary_line=summary_line)
