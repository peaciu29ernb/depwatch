"""Tests for depwatch.scanner."""

from __future__ import annotations

from pathlib import Path

import pytest

from depwatch.scanner import FoundDepFile, ScanResult, scan_repo


@pytest.fixture()
def repo_dir(tmp_path: Path) -> Path:
    """Create a fake repo with several dependency files at various depths."""
    (repo := tmp_path / "myrepo").mkdir()
    (repo / "requirements.txt").write_text("requests==2.31.0\n")
    (repo / "package.json").write_text('{"name": "myrepo"}\n')

    sub = repo / "services" / "api"
    sub.mkdir(parents=True)
    (sub / "Pipfile").write_text('[packages]\nflask = "*"\n')

    # Should be ignored — too deep (depth == max_depth)
    deep = repo / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "go.mod").write_text("module example.com/m\n")

    # Hidden dir should be skipped
    hidden = repo / ".hidden"
    hidden.mkdir()
    (hidden / "Gemfile").write_text("gem 'rails'\n")

    return repo


def test_scan_repo_returns_scan_result(repo_dir: Path) -> None:
    result = scan_repo(repo_dir)
    assert isinstance(result, ScanResult)
    assert result.repo_path == repo_dir.resolve()


def test_scan_repo_finds_known_dep_files(repo_dir: Path) -> None:
    result = scan_repo(repo_dir)
    filenames = {f.filename for f in result.dep_files}
    assert "requirements.txt" in filenames
    assert "package.json" in filenames
    assert "Pipfile" in filenames


def test_scan_repo_respects_max_depth(repo_dir: Path) -> None:
    result = scan_repo(repo_dir, max_depth=3)
    filenames = {f.filename for f in result.dep_files}
    # go.mod lives at depth 3 which equals max_depth — should be excluded
    assert "go.mod" not in filenames


def test_scan_repo_skips_hidden_dirs(repo_dir: Path) -> None:
    result = scan_repo(repo_dir)
    filenames = {f.filename for f in result.dep_files}
    assert "Gemfile" not in filenames


def test_found_dep_file_ecosystem(repo_dir: Path) -> None:
    result = scan_repo(repo_dir)
    by_name = {f.filename: f for f in result.dep_files}
    assert by_name["requirements.txt"].ecosystem == "pip"
    assert by_name["package.json"].ecosystem == "npm"
    assert by_name["Pipfile"].ecosystem == "pipenv"


def test_ecosystems_property_unique(repo_dir: Path) -> None:
    result = scan_repo(repo_dir)
    ecosystems = result.ecosystems
    assert len(ecosystems) == len(set(ecosystems))


def test_scan_repo_raises_for_missing_path(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        scan_repo(tmp_path / "nonexistent")


def test_scan_repo_raises_for_file_path(tmp_path: Path) -> None:
    """scan_repo should raise NotADirectoryError when given a file, not a dir."""
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("hello\n")
    with pytest.raises(NotADirectoryError):
        scan_repo(file_path)
