"""Format a TrendResult for human-readable output."""
from __future__ import annotations

from depwatch.trend import TrendResult

_ARROWS = {
    "rising": "\u2197",   # ↗
    "falling": "\u2198",  # ↘
    "stable": "\u2192",   # →
}


def format_trend_oneline(result: TrendResult) -> str:
    """Return a compact single-line summary, e.g. '→ stable | issues: 0 | vuln: 0 | outdated: 0'."""
    if not result.has_data:
        return "trend: insufficient data"

    arrow = _ARROWS.get(result.direction, "?")
    sign = lambda n: f"+{n}" if n > 0 else str(n)
    return (
        f"{arrow} {result.direction} | "
        f"issues: {sign(result.delta_issues)} | "
        f"vuln: {sign(result.delta_vulnerable)} | "
        f"outdated: {sign(result.delta_outdated)}"
    )


def format_trend_summary(result: TrendResult) -> str:
    """Return a multi-line trend report."""
    lines: list[str] = ["=== Trend Analysis ==="]

    if not result.has_data:
        lines.append("  Not enough data points to compute trend.")
        return "\n".join(lines)

    lines.append(f"  Direction   : {result.direction}")
    lines.append(f"  Δ issues    : {result.delta_issues:+d}")
    lines.append(f"  Δ vulnerable: {result.delta_vulnerable:+d}")
    lines.append(f"  Δ outdated  : {result.delta_outdated:+d}")
    lines.append(f"  Data points : {len(result.points)}")
    return "\n".join(lines)
