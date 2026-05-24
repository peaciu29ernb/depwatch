"""Tests for depwatch.alert_policy."""
import pytest

from depwatch.alert_policy import AlertDecision, AlertPolicy, evaluate_policy
from depwatch.checker import CheckResult, PackageIssue
from depwatch.reporter import Report
from depwatch.scanner import FoundDepFile


def _dep_file(repo: str = "repo") -> FoundDepFile:
    return FoundDepFile(path=f"/repos/{repo}/requirements.txt", ecosystem="pip")


def _issue(outdated: bool = False, vulnerable: bool = False) -> PackageIssue:
    return PackageIssue(
        package="pkg",
        current_version="1.0.0",
        latest_version="2.0.0",
        is_outdated=outdated,
        is_vulnerable=vulnerable,
    )


def _report(issues=(), repo="repo") -> Report:
    dep = _dep_file(repo)
    cr = CheckResult(dep_file=dep, issues=list(issues), repo=repo)
    return Report(check_results=[cr])


# ── basic threshold tests ──────────────────────────────────────────────────

def test_evaluate_policy_alerts_when_issues_meet_threshold():
    report = _report(issues=[_issue(outdated=True)])
    decision = evaluate_policy(report, AlertPolicy(min_issues=1))
    assert decision.should_alert is True


def test_evaluate_policy_suppresses_below_threshold():
    report = _report(issues=[])
    decision = evaluate_policy(report, AlertPolicy(min_issues=1))
    assert decision.should_alert is False


def test_evaluate_policy_reason_included():
    report = _report(issues=[_issue(outdated=True)])
    decision = evaluate_policy(report, AlertPolicy(min_issues=1))
    assert "1" in decision.reason


# ── vulnerable threshold ───────────────────────────────────────────────────

def test_evaluate_policy_vulnerable_threshold_triggers():
    report = _report(issues=[_issue(vulnerable=True)])
    policy = AlertPolicy(min_issues=999, min_vulnerable=1)
    decision = evaluate_policy(report, policy)
    assert decision.should_alert is True
    assert "vulnerable" in decision.reason


def test_evaluate_policy_vulnerable_threshold_not_met():
    report = _report(issues=[_issue(outdated=True)])
    policy = AlertPolicy(min_issues=999, min_vulnerable=1)
    decision = evaluate_policy(report, policy)
    assert decision.should_alert is False


# ── outdated threshold ─────────────────────────────────────────────────────

def test_evaluate_policy_outdated_threshold_triggers():
    report = _report(issues=[_issue(outdated=True), _issue(outdated=True)])
    policy = AlertPolicy(min_issues=999, min_outdated=2)
    decision = evaluate_policy(report, policy)
    assert decision.should_alert is True


# ── always_alert_repos ─────────────────────────────────────────────────────

def test_evaluate_policy_always_alert_repo_triggers_regardless():
    report = _report(issues=[_issue(outdated=True)], repo="critical-service")
    policy = AlertPolicy(min_issues=999, always_alert_repos=["critical-service"])
    decision = evaluate_policy(report, policy)
    assert decision.should_alert is True
    assert "critical-service" in decision.reason


def test_evaluate_policy_always_alert_repo_no_issues_does_not_trigger():
    report = _report(issues=[], repo="critical-service")
    policy = AlertPolicy(min_issues=999, always_alert_repos=["critical-service"])
    decision = evaluate_policy(report, policy)
    # repo has no issues so always_alert should not fire
    assert decision.should_alert is False


def test_alert_decision_bool_true():
    d = AlertDecision(should_alert=True, reason="x")
    assert bool(d) is True


def test_alert_decision_bool_false():
    d = AlertDecision(should_alert=False, reason="x")
    assert bool(d) is False
