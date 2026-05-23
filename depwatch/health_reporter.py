"""Formats a HealthStatus into human-readable text for console or notifier output."""
from __future__ import annotations

from depwatch.health import HealthStatus

_DATE_FMT = "%Y-%m-%d %H:%M:%S UTC"


def _fmt_dt(dt) -> str:
    if dt is None:
        return "never"
    return dt.strftime(_DATE_FMT)


def _fmt_uptime(seconds: float) -> str:
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def format_health(status: HealthStatus) -> str:
    """Return a multi-line health report string."""
    lines: list[str] = [
        "=== depwatch health ===",
        f"Status          : {'OK' if status.healthy else 'DEGRADED'}",
        f"Uptime          : {_fmt_uptime(status.uptime_seconds)}",
        f"Total cycles    : {status.total_cycles}",
        f"Total issues    : {status.total_issues_seen}",
        f"Consec. failures: {status.consecutive_failures}",
        f"Last success    : {_fmt_dt(status.last_success)}",
        f"Last failure    : {_fmt_dt(status.last_failure)}",
    ]
    if status.notes:
        lines.append("Notes:")
        for note in status.notes:
            lines.append(f"  - {note}")
    return "\n".join(lines)


def format_health_oneline(status: HealthStatus) -> str:
    """Return a compact single-line health summary."""
    return status.summary_line
