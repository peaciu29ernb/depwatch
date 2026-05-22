"""Tests for the depwatch daemon loop."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from depwatch.daemon import DaemonState, run_cycle, run_daemon


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path, interval: int = 60):
    """Return a minimal DepwatchConfig-like mock."""
    repo = MagicMock()
    repo.name = "test-repo"
    repo.path = str(tmp_path)

    cfg = MagicMock()
    cfg.repos = [repo]
    cfg.max_depth = 3
    cfg.interval = interval
    return cfg


# ---------------------------------------------------------------------------
# DaemonState
# ---------------------------------------------------------------------------

def test_daemon_state_defaults():
    state = DaemonState()
    assert state.running is False
    assert state.cycles_completed == 0
    assert state.last_run_ts is None
    assert state.errors == []


# ---------------------------------------------------------------------------
# run_cycle
# ---------------------------------------------------------------------------

@patch("depwatch.daemon.build_report")
@patch("depwatch.daemon.check_dep_file")
@patch("depwatch.daemon.scan_repo")
def test_run_cycle_returns_true_on_success(mock_scan, mock_check, mock_report, tmp_path):
    mock_scan.return_value = MagicMock(dep_files=[MagicMock()])
    mock_check.return_value = MagicMock()
    mock_report.return_value = MagicMock()
    notifier = MagicMock()

    config = _make_config(tmp_path)
    result = run_cycle(config, notifier)

    assert result is True
    notifier.notify.assert_called_once()


@patch("depwatch.daemon.build_report")
@patch("depwatch.daemon.scan_repo")
def test_run_cycle_returns_false_on_scan_error(mock_scan, mock_report, tmp_path):
    mock_scan.side_effect = RuntimeError("disk error")
    mock_report.return_value = MagicMock()
    notifier = MagicMock()

    config = _make_config(tmp_path)
    result = run_cycle(config, notifier)

    assert result is False
    # notify is still called even when a repo fails
    notifier.notify.assert_called_once()


# ---------------------------------------------------------------------------
# run_daemon
# ---------------------------------------------------------------------------

@patch("depwatch.daemon.Notifier")
@patch("depwatch.daemon.run_cycle", return_value=True)
@patch("depwatch.daemon.load_config")
def test_run_daemon_once_completes_one_cycle(mock_load, mock_cycle, mock_notifier_cls, tmp_path):
    mock_load.return_value = _make_config(tmp_path)
    mock_notifier_cls.from_config.return_value = MagicMock()

    state = run_daemon(str(tmp_path / "depwatch.toml"), once=True)

    assert state.cycles_completed == 1
    assert state.running is False
    assert state.last_run_ts is not None


@patch("depwatch.daemon.Notifier")
@patch("depwatch.daemon.run_cycle", return_value=False)
@patch("depwatch.daemon.load_config")
def test_run_daemon_records_errors(mock_load, mock_cycle, mock_notifier_cls, tmp_path):
    mock_load.return_value = _make_config(tmp_path)
    mock_notifier_cls.from_config.return_value = MagicMock()

    state = run_daemon(str(tmp_path / "depwatch.toml"), once=True)

    assert len(state.errors) == 1


@patch("depwatch.daemon.Notifier")
@patch("depwatch.daemon.run_cycle", return_value=True)
@patch("depwatch.daemon.load_config")
def test_run_daemon_uses_config_interval(mock_load, mock_cycle, mock_notifier_cls, tmp_path):
    cfg = _make_config(tmp_path, interval=30)
    mock_load.return_value = cfg
    mock_notifier_cls.from_config.return_value = MagicMock()

    # interval kwarg should override config value
    with patch("depwatch.daemon.time.sleep") as mock_sleep:
        # run two cycles then stop
        call_count = {"n": 0}

        def fake_cycle(config, notifier):
            call_count["n"] += 1
            if call_count["n"] >= 2:
                raise KeyboardInterrupt
            return True

        mock_cycle.side_effect = fake_cycle
        state = run_daemon(str(tmp_path / "depwatch.toml"), interval=10)

    mock_sleep.assert_called_with(10)
