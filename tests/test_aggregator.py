"""Tests for depwatch.aggregator."""

import pytest

from depwatch.aggregator import AggregationResult, aggregate, build_report
from depwatch.checker import CheckResult, PackageIssue
from depwatch.scanner import FoundDepFile, ScanResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dep_file(name: str = "requirements.txt") -> FoundDepFile:
    return FoundDepFile(path=f"/repo/{name}", ecosystem="pip")


def _issue(name: str = "requests", outdated: bool = True, vulnerable: bool = False) -> PackageIssue:
    return PackageIssue(package_name=name, current_version="1.0.0", is_outdated=outdated, is_vulnerable=vulnerable)


def _check_result(issues=None, errors=None) -> CheckResult:
    return CheckResult(issues=issues or [], errors=errors or [])


def _scan_result(errors=None) -> ScanResult:
    return ScanResult(dep_files=[_dep_file()], errors=errors or [])


# ---------------------------------------------------------------------------
# AggregationResult tests
# ---------------------------------------------------------------------------

def test_all_issues_empty_when_no_check_results():
    agg = AggregationResult(repo_name="myrepo", scan_result=_scan_result())
    assert agg.all_issues == []


def test_all_issues_flattens_multiple_check_results():
    cr1 = _check_result(issues=[_issue("requests")])
    cr2 = _check_result(issues=[_issue("flask"), _issue("django")])
    agg = AggregationResult(repo_name="myrepo", scan_result=_scan_result(), check_results=[cr1, cr2])
    assert len(agg.all_issues) == 3


def test_has_errors_false_when_no_errors():
    agg = AggregationResult(repo_name="myrepo", scan_result=_scan_result())
    assert agg.has_errors is False


def test_has_errors_true_when_errors_present():
    agg = AggregationResult(repo_name="myrepo", scan_result=_scan_result(), errors=["something went wrong"])
    assert agg.has_errors is True


# ---------------------------------------------------------------------------
# aggregate() tests
# ---------------------------------------------------------------------------

def test_aggregate_returns_aggregation_result():
    result = aggregate("myrepo", _scan_result(), [])
    assert isinstance(result, AggregationResult)
    assert result.repo_name == "myrepo"


def test_aggregate_merges_scan_and_check_errors():
    scan = _scan_result(errors=["scan error"])
    cr = _check_result(errors=["check error"])
    result = aggregate("myrepo", scan, [cr])
    assert "scan error" in result.errors
    assert "check error" in result.errors


def test_aggregate_no_errors_when_clean():
    result = aggregate("myrepo", _scan_result(), [_check_result()])
    assert result.errors == []


# ---------------------------------------------------------------------------
# build_report() tests
# ---------------------------------------------------------------------------

def test_build_report_empty_aggregations():
    report = build_report([])
    assert report.total_issues == 0
    assert report.errors == []


def test_build_report_collects_all_issues():
    agg1 = aggregate("repo1", _scan_result(), [_check_result(issues=[_issue("requests")])])
    agg2 = aggregate("repo2", _scan_result(), [_check_result(issues=[_issue("flask"), _issue("django")])])
    report = build_report([agg1, agg2])
    assert report.total_issues == 3


def test_build_report_collects_all_errors():
    agg = aggregate("repo1", _scan_result(errors=["oops"]), [_check_result(errors=["bad"])])
    report = build_report([agg])
    assert len(report.errors) == 2
