"""Daemon loop that periodically scans repos and sends notifications."""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from depwatch.config import DepwatchConfig, load_config
from depwatch.scanner import scan_repo
from depwatch.checker import check_dep_file
from depwatch.reporter import build_report
from depwatch.notifier import Notifier

logger = logging.getLogger(__name__)


@dataclass
class DaemonState:
    """Tracks runtime state of the daemon."""
    running: bool = False
    cycles_completed: int = 0
    last_run_ts: Optional[float] = None
    errors: list = field(default_factory=list)


def run_cycle(config: DepwatchConfig, notifier: Notifier) -> bool:
    """Run a single scan-check-notify cycle across all configured repos.

    Returns True if the cycle completed without errors, False otherwise.
    """
    check_results = []
    success = True

    for repo in config.repos:
        logger.info("Scanning repo: %s at %s", repo.name, repo.path)
        try:
            scan_result = scan_repo(repo.path, max_depth=config.max_depth)
            for dep_file in scan_result.dep_files:
                result = check_dep_file(dep_file)
                check_results.append(result)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error processing repo %s: %s", repo.name, exc)
            success = False

    report = build_report(check_results)
    notifier.notify(report)
    return success


def run_daemon(
    config_path: str,
    interval: Optional[int] = None,
    *,
    once: bool = False,
) -> DaemonState:
    """Start the depwatch daemon.

    Args:
        config_path: Path to the depwatch config file.
        interval: Override poll interval in seconds (uses config value if None).
        once: If True, run a single cycle then exit (useful for CI/testing).
    """
    config = load_config(config_path)
    poll_interval = interval if interval is not None else config.interval
    notifier = Notifier.from_config(config)
    state = DaemonState(running=True)

    logger.info(
        "depwatch daemon starting — %d repo(s), interval=%ds",
        len(config.repos),
        poll_interval,
    )

    try:
        while state.running:
            ok = run_cycle(config, notifier)
            state.cycles_completed += 1
            state.last_run_ts = time.time()
            if not ok:
                state.errors.append(state.last_run_ts)

            if once:
                state.running = False
            else:
                logger.debug("Sleeping %ds until next cycle.", poll_interval)
                time.sleep(poll_interval)
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user.")
        state.running = False

    return state
