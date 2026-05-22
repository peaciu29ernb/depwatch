"""Formats and outputs CheckResult summaries to stdout or a log."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from depwatch.checker import CheckResult

logger = logging.getLogger(__name__)


@dataclass
class Report:
    repo_name: str
    results: list[CheckResult]

    @property
    def total_issues(self) -> int:
        return sum(len(r.issues) for r in self.results)

    @property
    def total_vulnerable(self) -> int:
        return sum(len(r.vulnerable) for r in self.results)

    @property
    def total_outdated(self) -> int:
        return sum(len(r.outdated) for r in self.results)

    @property
    def errors(self) -> list[str]:
        return [r.error for r in self.results if r.error]


def build_report(repo_name: str, results: Iterable[CheckResult]) -> Report:
    return Report(repo_name=repo_name, results=list(results))


def format_report(report: Report) -> str:
    """Return a human-readable summary string for the report."""
    lines: list[str] = [
        f"=== depwatch report: {report.repo_name} ===",
        f"Files checked : {len(report.results)}",
        f"Total issues  : {report.total_issues} "
        f"(vulnerable={report.total_vulnerable}, outdated={report.total_outdated})",
    ]

    for result in report.results:
        if result.error:
            lines.append(f"  [ERROR] {result.dep_file.filename}: {result.error}")
            continue
        if not result.has_issues:
            lines.append(f"  [OK]    {result.dep_file.filename}")
            continue
        lines.append(f"  [WARN]  {result.dep_file.filename}")
        for issue in result.vulnerable:
            cves = ", ".join(issue.vulnerabilities)
            lines.append(f"    VULNERABLE  {issue.name}=={issue.current_version} ({cves})")
        for issue in result.outdated:
            lines.append(
                f"    OUTDATED    {issue.name}=={issue.current_version} "
                f"-> {issue.latest_version}"
            )

    if report.errors:
        lines.append(f"Errors ({len(report.errors)}): " + "; ".join(report.errors))

    return "\n".join(lines)


def emit_report(report: Report, *, verbose: bool = False) -> None:
    """Log the formatted report at appropriate log levels."""
    text = format_report(report)
    if report.total_issues > 0 or report.errors:
        logger.warning(text)
    else:
        logger.info(text)
    if verbose:
        print(text)
