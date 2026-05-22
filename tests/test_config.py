"""Tests for depwatch configuration loader."""

import os
import textwrap
import pytest

from depwatch.config import load_config, DepwatchConfig, RepoConfig


@pytest.fixture
def config_file(tmp_path):
    """Write a sample config file and return its path."""
    content = textwrap.dedent("""\
        repos:
          - path: /home/user/projects/api
            name: my-api
          - path: /home/user/projects/frontend
            enabled: false
        check_interval: 1800
        alert_email: ops@example.com
        vulnerability_check: true
        outdated_check: false
        log_level: DEBUG
    """)
    cfg = tmp_path / "depwatch.yml"
    cfg.write_text(content)
    return str(cfg)


def test_load_config_returns_depwatch_config(config_file):
    cfg = load_config(config_file)
    assert isinstance(cfg, DepwatchConfig)


def test_load_config_repos(config_file):
    cfg = load_config(config_file)
    assert len(cfg.repos) == 2
    assert cfg.repos[0].name == "my-api"
    assert cfg.repos[1].enabled is False


def test_repo_name_defaults_to_dirname(config_file):
    cfg = load_config(config_file)
    assert cfg.repos[1].name == "frontend"


def test_load_config_scalar_fields(config_file):
    cfg = load_config(config_file)
    assert cfg.check_interval == 1800
    assert cfg.alert_email == "ops@example.com"
    assert cfg.vulnerability_check is True
    assert cfg.outdated_check is False
    assert cfg.log_level == "DEBUG"


def test_load_config_defaults(tmp_path):
    cfg_file = tmp_path / "minimal.yml"
    cfg_file.write_text("repos: []\n")
    cfg = load_config(str(cfg_file))
    assert cfg.check_interval == 3600
    assert cfg.alert_email is None
    assert cfg.vulnerability_check is True
    assert cfg.outdated_check is True
    assert cfg.log_level == "INFO"


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/depwatch.yml")


def test_load_config_invalid_yaml(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("- just a list\n- not a mapping\n")
    with pytest.raises(ValueError):
        load_config(str(bad))
