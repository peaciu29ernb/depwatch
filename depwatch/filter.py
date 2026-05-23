"""Filter module for depwatch — selects issues based on severity, ecosystem, and package rules."""

from dataclasses import dataclass, field
from typing import List, Optional

from depwatch.checker import PackageIssue


@dataclass
class FilterConfig:
    min_severity: Optional[str] = None  # "outdated", "vulnerable", or None (any)
    ecosystems: List[str] = field(default_factory=list)  # empty = all
    exclude_packages: List[str] = field(default_factory=list)
    only_vulnerable: bool = False
    only_outdated: bool = False


@dataclass
class FilterResult:
    accepted: List[PackageIssue] = field(default_factory=list)
    rejected: List[PackageIssue] = field(default_factory=list)

    @property
    def total_accepted(self) -> int:
        return len(self.accepted)

    @property
    def total_rejected(self) -> int:
        return len(self.rejected)


def _matches_severity(issue: PackageIssue, config: FilterConfig) -> bool:
    if config.only_vulnerable and not issue.is_vulnerable:
        return False
    if config.only_outdated and not issue.is_outdated:
        return False
    return True


def _matches_ecosystem(issue: PackageIssue, config: FilterConfig) -> bool:
    if not config.ecosystems:
        return True
    return issue.ecosystem in config.ecosystems


def _matches_exclusion(issue: PackageIssue, config: FilterConfig) -> bool:
    return issue.package_name not in config.exclude_packages


def apply_filter(issues: List[PackageIssue], config: FilterConfig) -> FilterResult:
    """Apply filter rules to a list of PackageIssue objects."""
    result = FilterResult()
    for issue in issues:
        if (
            _matches_severity(issue, config)
            and _matches_ecosystem(issue, config)
            and _matches_exclusion(issue, config)
        ):
            result.accepted.append(issue)
        else:
            result.rejected.append(issue)
    return result
