"""Formats a MetricsStore into human-readable text for the console or logs."""
from __future__ import annotations

from depwatch.metrics import MetricsStore


def _bar(value: int, max_value: int, width: int = 20) -> str:
    """Render a simple ASCII bar."""
    if max_value == 0:
        filled = 0
    else:
        filled = int(round(value / max_value * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def format_metrics_summary(store: MetricsStore) -> str:
    """Return a multi-line summary string for the given MetricsStore."""
    d = store.as_dict()
    lines = [
        "=== depwatch metrics ===",
        f"  Cycles run          : {d['total_cycles']}",
        f"  Total issues seen   : {d['total_issues_seen']}",
        f"  Total errors seen   : {d['total_errors_seen']}",
        f"  Avg cycle duration  : {d['average_duration_seconds']}s",
    ]
    counts = store.issue_counts_by_cycle
    if counts:
        max_c = max(counts)
        lines.append("  Issues per cycle:")
        for i, c in enumerate(counts, start=1):
            lines.append(f"    #{i:>3}  {_bar(c, max_c)}  {c}")
    latest = store.latest()
    if latest:
        lines.append(
            f"  Last run            : {latest.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )
    return "\n".join(lines)


def format_metrics_oneline(store: MetricsStore) -> str:
    """Return a compact single-line summary."""
    d = store.as_dict()
    return (
        f"cycles={d['total_cycles']} "
        f"issues={d['total_issues_seen']} "
        f"errors={d['total_errors_seen']} "
        f"avg_dur={d['average_duration_seconds']}s"
    )
