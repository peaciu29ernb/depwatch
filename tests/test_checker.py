"""Tests for depwatch.checker."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import (
    CheckResult,
    PackageIssue,
    check_dep_file,
)
from depwatch.scanner import FoundDepFile


@pytest.fixture()
def pip_dep_file(tmp_path: Path) -> FoundDepFile:
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.28.0\n")
    return FoundDepFile(path=req, ecosystem="pip", filename="requirements.txt")


@pytest.fixture()
def npm_dep_file(tmp_path: Path) -> FoundDepFile:
    pkg = tmp_path / "package.json"
    pkg.write_text('{"dependencies": {}}\n')
    return FoundDepFile(path=pkg, ecosystem="npm", filename="package.json")


def test_check_result_has_issues_false_when_empty(pip_dep_file):
    result = CheckResult(dep_file=pip_dep_file)
    assert result.has_issues is False


def test_check_result_has_issues_true_with_issue(pip_dep_file):
    issue = PackageIssue(name="requests", current_version="2.28.0", vulnerabilities=["CVE-2023-0001"])
    result = CheckResult(dep_file=pip_dep_file, issues=[issue])
    assert result.has_issues is True


def test_package_issue_is_outdated():
    issue = PackageIssue(name="requests", current_version="2.28.0", latest_version="2.31.0")
    assert issue.is_outdated is True


def test_package_issue_not_outdated_when_versions_match():
    issue = PackageIssue(name="requests", current_version="2.31.0", latest_version="2.31.0")
    assert issue.is_outdated is False


def test_package_issue_is_vulnerable():
    issue = PackageIssue(name="requests", current_version="2.28.0", vulnerabilities=["CVE-2023-0001"])
    assert issue.is_vulnerable is True


def test_check_dep_file_unknown_ecosystem_returns_error(npm_dep_file):
    result = check_dep_file(npm_dep_file)
    assert result.error is not None
    assert "npm" in result.error
    assert result.has_issues is False


def test_check_dep_file_pip_audit_not_found(pip_dep_file):
    with patch("depwatch.checker.subprocess.run", side_effect=FileNotFoundError):
        result = check_dep_file(pip_dep_file)
    assert result.error == "pip-audit not found"


def test_check_dep_file_pip_returns_vulnerabilities(pip_dep_file):
    mock_output = json_output = (
        '{"dependencies": [{"name": "requests", "version": "2.28.0", '
        '"vulns": [{"id": "CVE-2023-0001"}]}]}'
    )
    mock_proc = MagicMock()
    mock_proc.stdout = mock_output
    mock_proc.returncode = 1

    with patch("depwatch.checker.subprocess.run", return_value=mock_proc):
        result = check_dep_file(pip_dep_file)

    assert result.error is None
    assert len(result.vulnerable) == 1
    assert result.vulnerable[0].name == "requests"
    assert "CVE-2023-0001" in result.vulnerable[0].vulnerabilities


def test_check_result_outdated_filters_correctly(pip_dep_file):
    issues = [
        PackageIssue(name="requests", current_version="2.28.0", latest_version="2.31.0"),
        PackageIssue(name="flask", current_version="2.3.0", latest_version="2.3.0"),
    ]
    result = CheckResult(dep_file=pip_dep_file, issues=issues)
    assert len(result.outdated) == 1
    assert result.outdated[0].name == "requests"
