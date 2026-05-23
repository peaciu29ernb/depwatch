"""Pipeline module — wires scanner, parser, checker, filter, and aggregator into one call."""

from dataclasses import dataclass, field
from typing import List, Optional

from depwatch.scanner import scan_repo, ScanResult
from depwatch.parser import parse_dep_file
from depwatch.checker import check_packages
from depwatch.filter import FilterConfig, FilterResult, apply_filter
from depwatch.aggregator import AggregationResult, aggregate, build_report
from depwatch.reporter import Report


@dataclass
class PipelineConfig:
    repo_path: str
    max_depth: int = 3
    filter_config: FilterConfig = field(default_factory=FilterConfig)


@dataclass
class PipelineResult:
    scan: Optional[ScanResult] = None
    filter_result: Optional[FilterResult] = None
    aggregation: Optional[AggregationResult] = None
    report: Optional[Report] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Execute the full depwatch pipeline for a single repository."""
    result = PipelineResult()

    try:
        scan = scan_repo(config.repo_path, max_depth=config.max_depth)
        result.scan = scan
    except Exception as exc:  # noqa: BLE001
        result.error = f"Scan failed: {exc}"
        return result

    check_results = []
    for dep_file in scan.dep_files:
        try:
            parsed = parse_dep_file(dep_file)
            if parsed.ok:
                checked = check_packages(parsed.packages, dep_file)
                check_results.append(checked)
        except Exception as exc:  # noqa: BLE001
            # non-fatal: record error but continue
            check_results.append(
                type(
                    "_ErrResult",
                    (),
                    {"issues": [], "error": str(exc), "dep_file": dep_file},
                )()
            )

    aggregation = aggregate(check_results)
    result.aggregation = aggregation

    all_issues = aggregation.all_issues
    filtered = apply_filter(all_issues, config.filter_config)
    result.filter_result = filtered

    result.report = build_report(aggregation, repo_path=config.repo_path)
    return result
