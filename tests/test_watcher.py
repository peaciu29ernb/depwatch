"""Tests for depwatch.watcher."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from depwatch.scanner import FoundDepFile
from depwatch.watcher import (
    ChangeSet,
    WatcherState,
    detect_changes,
    _checksum,
    _snapshot,
)


@pytest.fixture()
def tmp_dep(tmp_path: Path) -> Path:
    f = tmp_path / "requirements.txt"
    f.write_text("requests==2.28.0\n")
    return f


def _found(path: str) -> FoundDepFile:
    return FoundDepFile(path=path, ecosystem="pip")


# --- ChangeSet ---

def test_changeset_has_changes_false_when_empty():
    cs = ChangeSet()
    assert cs.has_changes is False


def test_changeset_has_changes_true_with_added():
    cs = ChangeSet(added=["/some/file"])
    assert cs.has_changes is True


def test_changeset_has_changes_true_with_modified():
    cs = ChangeSet(modified=["/some/file"])
    assert cs.has_changes is True


def test_changeset_has_changes_true_with_removed():
    cs = ChangeSet(removed=["/some/file"])
    assert cs.has_changes is True


# --- WatcherState ---

def test_watcher_state_get_missing_returns_none():
    state = WatcherState()
    assert state.get("/nonexistent") is None


# --- _checksum ---

def test_checksum_returns_string(tmp_dep: Path):
    result = _checksum(str(tmp_dep))
    assert isinstance(result, str) and len(result) == 64


def test_checksum_changes_on_content_change(tmp_dep: Path):
    c1 = _checksum(str(tmp_dep))
    tmp_dep.write_text("flask==2.3.0\n")
    c2 = _checksum(str(tmp_dep))
    assert c1 != c2


# --- detect_changes ---

def test_detect_changes_new_file_is_added(tmp_dep: Path):
    state = WatcherState()
    cs = detect_changes([_found(str(tmp_dep))], state)
    assert str(tmp_dep) in cs.added
    assert cs.modified == []


def test_detect_changes_unchanged_file_not_reported(tmp_dep: Path):
    state = WatcherState()
    detect_changes([_found(str(tmp_dep))], state)
    cs = detect_changes([_found(str(tmp_dep))], state)
    assert cs.has_changes is False


def test_detect_changes_modified_file_reported(tmp_dep: Path):
    state = WatcherState()
    detect_changes([_found(str(tmp_dep))], state)
    tmp_dep.write_text("flask==2.3.0\n")
    cs = detect_changes([_found(str(tmp_dep))], state)
    assert str(tmp_dep) in cs.modified


def test_detect_changes_removed_file_reported(tmp_dep: Path):
    state = WatcherState()
    detect_changes([_found(str(tmp_dep))], state)
    cs = detect_changes([], state)
    assert str(tmp_dep) in cs.removed
    assert state.get(str(tmp_dep)) is None


def test_detect_changes_missing_file_skipped(tmp_path: Path):
    ghost = str(tmp_path / "ghost.txt")
    state = WatcherState()
    cs = detect_changes([_found(ghost)], state)
    assert ghost not in cs.added
