"""Tests for depwatch.audit_reporter."""

from __future__ import annotations

from pathlib import Path

import pytest

from depwatch.audit_log import AuditLog, make_entry
from depwatch.audit_reporter import AuditSummary, summarise_log, top_repos_by_issues


@pytest.fixture()
def empty_log(tmp_path: Path) -> AuditLog:
    return AuditLog(path=tmp_path / "audit.json")


@pytest.fixture()
def populated_log(tmp_path: Path) -> AuditLog:
    log = AuditLog(path=tmp_path / "audit.json")
    log.record(make_entry("repoA", 3, 2, 1, False))
    log.record(make_entry("repoB", 5, 3, 2, True))
    log.record(make_entry("repoA", 1, 1, 0, False))
    return log


# ---------------------------------------------------------------------------

def test_summarise_empty_log(empty_log: AuditLog) -> None:
    summary = summarise_log(empty_log)
    assert summary.total_cycles == 0
    assert summary.total_issues_seen == 0
    assert summary.total_errors == 0
    assert summary.repos == []
    assert summary.most_recent_timestamp == ""


def test_summarise_total_cycles(populated_log: AuditLog) -> None:
    assert summarise_log(populated_log).total_cycles == 3


def test_summarise_total_issues(populated_log: AuditLog) -> None:
    assert summarise_log(populated_log).total_issues_seen == 9


def test_summarise_total_errors(populated_log: AuditLog) -> None:
    assert summarise_log(populated_log).total_errors == 1


def test_summarise_repos_list(populated_log: AuditLog) -> None:
    repos = summarise_log(populated_log).repos
    assert repos.count("repoA") == 2
    assert repos.count("repoB") == 1


def test_summarise_most_recent_timestamp(populated_log: AuditLog) -> None:
    ts = summarise_log(populated_log).most_recent_timestamp
    assert ts != ""


def test_as_text_contains_key_info(populated_log: AuditLog) -> None:
    text = summarise_log(populated_log).as_text()
    assert "Cycles recorded" in text
    assert "repoA" in text


def test_top_repos_by_issues_ordering(populated_log: AuditLog) -> None:
    top = top_repos_by_issues(populated_log)
    # repoA: 3+1=4, repoB: 5  => repoB first
    assert top[0] == "repoB"
    assert top[1] == "repoA"


def test_top_repos_respects_n(populated_log: AuditLog) -> None:
    top = top_repos_by_issues(populated_log, n=1)
    assert len(top) == 1


def test_top_repos_empty_log(empty_log: AuditLog) -> None:
    assert top_repos_by_issues(empty_log) == []
