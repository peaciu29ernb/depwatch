"""Tests for depwatch.dedup."""
from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageIssue
from depwatch.scanner import FoundDepFile
from depwatch.dedup import DedupResult, DedupStats, dedup_issues


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _dep_file(name: str = "requirements.txt", ecosystem: str = "pip") -> FoundDepFile:
    return FoundDepFile(path=f"/repo/{name}", ecosystem=ecosystem)


def _issue(
    name: str = "requests",
    version: str = "2.0.0",
    ecosystem: str = "pip",
    outdated: bool = True,
    vulnerable: bool = False,
) -> PackageIssue:
    return PackageIssue(
        package_name=name,
        current_version=version,
        latest_version="3.0.0",
        ecosystem=ecosystem,
        is_outdated=outdated,
        is_vulnerable=vulnerable,
    )


def _result(issues: list) -> CheckResult:
    return CheckResult(dep_file=_dep_file(), issues=issues, errors=[])


# ---------------------------------------------------------------------------
# DedupStats
# ---------------------------------------------------------------------------

def test_dedup_stats_duplicate_rate_zero_when_no_issues():
    stats = DedupStats()
    assert stats.duplicate_rate == 0.0


def test_dedup_stats_duplicate_rate_calculated():
    stats = DedupStats(total_seen=4, total_duplicates=2, total_unique=2)
    assert stats.duplicate_rate == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# dedup_issues
# ---------------------------------------------------------------------------

def test_dedup_issues_empty_results():
    result = dedup_issues([])
    assert isinstance(result, DedupResult)
    assert result.issues == []
    assert result.stats.total_seen == 0


def test_dedup_issues_no_duplicates():
    issues = [_issue("requests"), _issue("flask")]
    result = dedup_issues([_result(issues)])
    assert result.stats.total_unique == 2
    assert result.stats.total_duplicates == 0


def test_dedup_issues_removes_exact_duplicates():
    issue = _issue("requests", "2.0.0")
    r1 = _result([issue])
    r2 = _result([issue])
    result = dedup_issues([r1, r2])
    assert result.stats.total_seen == 2
    assert result.stats.total_duplicates == 1
    assert result.stats.total_unique == 1
    assert len(result.issues) == 1


def test_dedup_issues_different_versions_not_duplicate():
    r1 = _result([_issue("requests", "2.0.0")])
    r2 = _result([_issue("requests", "2.1.0")])
    result = dedup_issues([r1, r2])
    assert result.stats.total_unique == 2
    assert result.stats.total_duplicates == 0


def test_dedup_issues_different_flags_not_duplicate():
    r1 = _result([_issue("requests", outdated=True, vulnerable=False)])
    r2 = _result([_issue("requests", outdated=False, vulnerable=True)])
    result = dedup_issues([r1, r2])
    assert result.stats.total_unique == 2


def test_dedup_issues_preserves_first_occurrence():
    issue = _issue("requests", "2.0.0")
    duplicate = _issue("requests", "2.0.0")
    result = dedup_issues([_result([issue]), _result([duplicate])])
    assert result.issues[0] is issue


def test_dedup_issues_multiple_check_results():
    r1 = _result([_issue("requests"), _issue("flask")])
    r2 = _result([_issue("flask"), _issue("django")])
    result = dedup_issues([r1, r2])
    assert result.stats.total_seen == 4
    assert result.stats.total_duplicates == 1
    assert result.stats.total_unique == 3
