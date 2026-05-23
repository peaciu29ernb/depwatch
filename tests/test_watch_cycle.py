"""Tests for depwatch.watch_cycle."""
from __future__ import annotations

from pathlib import Path

import pytest

from depwatch.scanner import FoundDepFile, ScanResult
from depwatch.watch_cycle import (
    WatchCycleState,
    evaluate_repo,
    evaluate_all_repos,
)


def _scan(dep_paths: list[str]) -> ScanResult:
    files = [FoundDepFile(path=p, ecosystem="pip") for p in dep_paths]
    return ScanResult(repo_path="/repo", dep_files=files)


@pytest.fixture()
def req_file(tmp_path: Path) -> Path:
    f = tmp_path / "requirements.txt"
    f.write_text("requests==2.28.0\n")
    return f


# --- WatchCycleState ---

def test_watch_cycle_state_creates_new_watcher_state():
    state = WatchCycleState()
    ws = state.state_for("my-repo")
    assert ws is not None


def test_watch_cycle_state_returns_same_instance():
    state = WatchCycleState()
    ws1 = state.state_for("my-repo")
    ws2 = state.state_for("my-repo")
    assert ws1 is ws2


# --- evaluate_repo ---

def test_evaluate_repo_new_file_not_skipped(req_file: Path):
    state = WatchCycleState()
    result = evaluate_repo("repo", _scan([str(req_file)]), state)
    assert result.skipped is False
    assert result.repo_name == "repo"


def test_evaluate_repo_unchanged_is_skipped(req_file: Path):
    state = WatchCycleState()
    evaluate_repo("repo", _scan([str(req_file)]), state)
    result = evaluate_repo("repo", _scan([str(req_file)]), state)
    assert result.skipped is True


def test_evaluate_repo_modified_not_skipped(req_file: Path):
    state = WatchCycleState()
    evaluate_repo("repo", _scan([str(req_file)]), state)
    req_file.write_text("flask==2.3.0\n")
    result = evaluate_repo("repo", _scan([str(req_file)]), state)
    assert result.skipped is False
    assert str(req_file) in result.changeset.modified


def test_evaluate_repo_empty_scan_no_changes():
    state = WatchCycleState()
    result = evaluate_repo("empty-repo", _scan([]), state)
    assert result.skipped is True


# --- evaluate_all_repos ---

def test_evaluate_all_repos_returns_result_per_repo(req_file: Path, tmp_path: Path):
    f2 = tmp_path / "package.json"
    f2.write_text('{"dependencies": {}}\n')
    state = WatchCycleState()
    scans = {
        "repo-a": _scan([str(req_file)]),
        "repo-b": _scan([str(f2)]),
    }
    results = evaluate_all_repos(scans, state)
    assert len(results) == 2
    names = {r.repo_name for r in results}
    assert names == {"repo-a", "repo-b"}


def test_evaluate_all_repos_empty_dict():
    state = WatchCycleState()
    results = evaluate_all_repos({}, state)
    assert results == []
