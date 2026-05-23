"""Tests for depwatch.audit_log."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.audit_log import AuditEntry, AuditLog, make_entry


@pytest.fixture()
def log_path(tmp_path: Path) -> Path:
    return tmp_path / "audit" / "audit.json"


@pytest.fixture()
def audit_log(log_path: Path) -> AuditLog:
    return AuditLog(path=log_path)


def _entry(repo: str = "myrepo", issues: int = 2) -> AuditEntry:
    return make_entry(
        repo=repo,
        total_issues=issues,
        total_outdated=1,
        total_vulnerable=1,
        had_errors=False,
    )


# ---------------------------------------------------------------------------

def test_audit_log_creates_parent_dir(log_path: Path) -> None:
    AuditLog(path=log_path)
    assert log_path.parent.exists()


def test_audit_log_starts_empty(audit_log: AuditLog) -> None:
    assert audit_log.entries() == []


def test_record_appends_entry(audit_log: AuditLog) -> None:
    audit_log.record(_entry())
    assert len(audit_log.entries()) == 1


def test_record_persists_to_disk(audit_log: AuditLog, log_path: Path) -> None:
    audit_log.record(_entry(repo="alpha"))
    raw = json.loads(log_path.read_text())
    assert raw[0]["repo"] == "alpha"


def test_reload_restores_entries(log_path: Path) -> None:
    log1 = AuditLog(path=log_path)
    log1.record(_entry(repo="beta"))

    log2 = AuditLog(path=log_path)
    assert len(log2.entries()) == 1
    assert log2.entries()[0].repo == "beta"


def test_last_returns_most_recent(audit_log: AuditLog) -> None:
    for i in range(5):
        audit_log.record(_entry(repo=f"repo{i}"))
    last = audit_log.last(3)
    assert len(last) == 3
    assert last[-1].repo == "repo4"


def test_max_entries_trims_oldest(log_path: Path) -> None:
    log = AuditLog(path=log_path, max_entries=3)
    for i in range(5):
        log.record(_entry(repo=f"r{i}"))
    assert len(log.entries()) == 3
    assert log.entries()[0].repo == "r2"


def test_make_entry_sets_timestamp() -> None:
    e = make_entry("x", 0, 0, 0, False)
    assert "T" in e.timestamp  # ISO-8601 contains T separator


def test_make_entry_optional_note() -> None:
    e = make_entry("x", 1, 1, 0, False, note="manual run")
    assert e.note == "manual run"


def test_corrupt_file_starts_empty(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("not valid json")
    log = AuditLog(path=log_path)
    assert log.entries() == []
