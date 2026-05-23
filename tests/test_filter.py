"""Tests for depwatch.filter module."""

import pytest
from depwatch.checker import PackageIssue
from depwatch.filter import FilterConfig, FilterResult, apply_filter


def _issue(
    name: str = "pkg",
    ecosystem: str = "pip",
    is_outdated: bool = False,
    is_vulnerable: bool = False,
) -> PackageIssue:
    return PackageIssue(
        package_name=name,
        ecosystem=ecosystem,
        current_version="1.0.0",
        latest_version="2.0.0" if is_outdated else "1.0.0",
        is_outdated=is_outdated,
        is_vulnerable=is_vulnerable,
        vulnerability_ids=["CVE-2024-001"] if is_vulnerable else [],
    )


def test_filter_result_defaults():
    result = FilterResult()
    assert result.total_accepted == 0
    assert result.total_rejected == 0


def test_apply_filter_accepts_all_by_default():
    issues = [_issue("a"), _issue("b"), _issue("c")]
    result = apply_filter(issues, FilterConfig())
    assert result.total_accepted == 3
    assert result.total_rejected == 0


def test_apply_filter_only_vulnerable():
    issues = [
        _issue("safe", is_outdated=True),
        _issue("vuln", is_vulnerable=True),
    ]
    result = apply_filter(issues, FilterConfig(only_vulnerable=True))
    assert result.total_accepted == 1
    assert result.accepted[0].package_name == "vuln"


def test_apply_filter_only_outdated():
    issues = [
        _issue("old", is_outdated=True),
        _issue("vuln", is_vulnerable=True),
    ]
    result = apply_filter(issues, FilterConfig(only_outdated=True))
    assert result.total_accepted == 1
    assert result.accepted[0].package_name == "old"


def test_apply_filter_by_ecosystem():
    issues = [
        _issue("pip-pkg", ecosystem="pip"),
        _issue("npm-pkg", ecosystem="npm"),
    ]
    result = apply_filter(issues, FilterConfig(ecosystems=["pip"]))
    assert result.total_accepted == 1
    assert result.accepted[0].ecosystem == "pip"


def test_apply_filter_multiple_ecosystems():
    issues = [
        _issue("a", ecosystem="pip"),
        _issue("b", ecosystem="npm"),
        _issue("c", ecosystem="cargo"),
    ]
    result = apply_filter(issues, FilterConfig(ecosystems=["pip", "npm"]))
    assert result.total_accepted == 2
    assert result.total_rejected == 1


def test_apply_filter_exclude_packages():
    issues = [_issue("requests"), _issue("flask"), _issue("django")]
    result = apply_filter(issues, FilterConfig(exclude_packages=["flask", "django"]))
    assert result.total_accepted == 1
    assert result.accepted[0].package_name == "requests"


def test_apply_filter_combined_rules():
    issues = [
        _issue("a", ecosystem="pip", is_vulnerable=True),
        _issue("b", ecosystem="pip", is_outdated=True),
        _issue("c", ecosystem="npm", is_vulnerable=True),
        _issue("skip", ecosystem="pip", is_vulnerable=True),
    ]
    config = FilterConfig(
        ecosystems=["pip"],
        only_vulnerable=True,
        exclude_packages=["skip"],
    )
    result = apply_filter(issues, config)
    assert result.total_accepted == 1
    assert result.accepted[0].package_name == "a"


def test_apply_filter_empty_input():
    result = apply_filter([], FilterConfig(only_vulnerable=True))
    assert result.total_accepted == 0
    assert result.total_rejected == 0
