"""Tests for depwatch.parser."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from depwatch.parser import parse_dep_file, ParseResult, ParsedPackage


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# requirements.txt
# ---------------------------------------------------------------------------

def test_parse_requirements_txt_returns_parse_result(tmp_repo: Path):
    req = tmp_repo / "requirements.txt"
    req.write_text("requests==2.31.0\n")
    result = parse_dep_file(req)
    assert isinstance(result, ParseResult)
    assert result.ecosystem == "pip"


def test_parse_requirements_txt_packages(tmp_repo: Path):
    req = tmp_repo / "requirements.txt"
    req.write_text("requests==2.31.0\nflask>=2.0\n")
    result = parse_dep_file(req)
    names = [p.name for p in result.packages]
    assert "requests" in names
    assert "flask" in names


def test_parse_requirements_txt_version(tmp_repo: Path):
    req = tmp_repo / "requirements.txt"
    req.write_text("django==4.2.1\n")
    result = parse_dep_file(req)
    assert result.packages[0].version == "4.2.1"


def test_parse_requirements_txt_skips_comments_and_blanks(tmp_repo: Path):
    req = tmp_repo / "requirements.txt"
    req.write_text("# this is a comment\n\nrequests==2.31.0\n")
    result = parse_dep_file(req)
    assert len(result.packages) == 1


def test_parse_requirements_txt_extras(tmp_repo: Path):
    req = tmp_repo / "requirements.txt"
    req.write_text("uvicorn[standard]==0.23.0\n")
    result = parse_dep_file(req)
    assert result.packages[0].extras == ["standard"]


def test_parse_requirements_txt_no_version(tmp_repo: Path):
    req = tmp_repo / "requirements.txt"
    req.write_text("boto3\n")
    result = parse_dep_file(req)
    assert result.packages[0].version is None


# ---------------------------------------------------------------------------
# package.json
# ---------------------------------------------------------------------------

def test_parse_package_json_returns_parse_result(tmp_repo: Path):
    pkg = tmp_repo / "package.json"
    pkg.write_text(json.dumps({"dependencies": {"express": "^4.18.2"}}))
    result = parse_dep_file(pkg)
    assert isinstance(result, ParseResult)
    assert result.ecosystem == "npm"


def test_parse_package_json_strips_semver_prefix(tmp_repo: Path):
    pkg = tmp_repo / "package.json"
    pkg.write_text(json.dumps({"dependencies": {"lodash": "^4.17.21"}}))
    result = parse_dep_file(pkg)
    assert result.packages[0].version == "4.17.21"


def test_parse_package_json_dev_dependencies(tmp_repo: Path):
    pkg = tmp_repo / "package.json"
    pkg.write_text(json.dumps({"devDependencies": {"jest": "~29.0.0"}}))
    result = parse_dep_file(pkg)
    names = [p.name for p in result.packages]
    assert "jest" in names


def test_parse_package_json_invalid_json(tmp_repo: Path):
    pkg = tmp_repo / "package.json"
    pkg.write_text("not valid json")
    result = parse_dep_file(pkg)
    assert not result.ok
    assert result.error is not None


# ---------------------------------------------------------------------------
# Unknown file
# ---------------------------------------------------------------------------

def test_parse_unknown_file_returns_error(tmp_repo: Path):
    unknown = tmp_repo / "Gemfile"
    unknown.write_text("gem 'rails'\n")
    result = parse_dep_file(unknown)
    assert not result.ok
    assert "No parser" in result.error
