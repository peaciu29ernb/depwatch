"""Aggregates scan and check results into a unified Report."""

from dataclasses import dataclass, field
from typing import List

from depwatch.checker import CheckResult, PackageIssue
from depwatch.reporter import Report
from depwatch.scanner import ScanResult


@dataclass
class AggregationResult:
    """Holds the aggregated output from one full daemon cycle."""

    repo_name: str
    scan_result: ScanResult
    check_results: List[CheckResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def all_issues(self) -> List[PackageIssue]:
        """Flatten all PackageIssue objects from every CheckResult."""
        issues: List[PackageIssue] = []
        for cr in self.check_results:
            issues.extend(cr.issues)
        return issues

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def aggregate(repo_name: str, scan_result: ScanResult, check_results: List[CheckResult]) -> AggregationResult:
    """Combine scan and check results for a single repo into an AggregationResult."""
    errors: List[str] = list(scan_result.errors)
    for cr in check_results:
        errors.extend(cr.errors)
    return AggregationResult(
        repo_name=repo_name,
        scan_result=scan_result,
        check_results=check_results,
        errors=errors,
    )


def build_report(aggregations: List[AggregationResult]) -> Report:
    """Build a top-level Report from a list of per-repo AggregationResults."""
    all_issues: List[PackageIssue] = []
    all_errors: List[str] = []

    for agg in aggregations:
        all_issues.extend(agg.all_issues)
        all_errors.extend(agg.errors)

    return Report(
        issues=all_issues,
        errors=all_errors,
    )
