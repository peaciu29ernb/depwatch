"""Wrapper around checker that caches results using ResultCache."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from depwatch.cache import ResultCache
from depwatch.checker import CheckResult, PackageIssue, check_dep_file
from depwatch.scanner import FoundDepFile


def _cache_key(dep_file: FoundDepFile) -> str:
    """Derive a stable cache key from the dep file path and its mtime."""
    path = Path(dep_file.filename)
    mtime = path.stat().st_mtime if path.exists() else 0.0
    return f"{dep_file.filename}:{mtime}"


def _serialise_result(result: CheckResult) -> dict:
    return {
        "dep_file": dep_file_dict(result.dep_file),
        "issues": [asdict(i) for i in result.issues],
        "error": result.error,
    }


def dep_file_dict(dep_file: FoundDepFile) -> dict:
    return {"filename": dep_file.filename, "ecosystem": dep_file.ecosystem}


def _deserialise_result(data: dict) -> CheckResult:
    df = FoundDepFile(
        filename=data["dep_file"]["filename"],
        ecosystem=data["dep_file"]["ecosystem"],
    )
    issues = [
        PackageIssue(
            name=i["name"],
            current_version=i["current_version"],
            latest_version=i.get("latest_version"),
            vulnerabilities=i.get("vulnerabilities", []),
            outdated=i["outdated"],
            vulnerable=i["vulnerable"],
        )
        for i in data["issues"]
    ]
    return CheckResult(dep_file=df, issues=issues, error=data.get("error"))


class CachedChecker:
    """Runs check_dep_file and caches results to avoid redundant network calls."""

    def __init__(self, cache: ResultCache) -> None:
        self.cache = cache
        self._cache_hits = 0
        self._cache_misses = 0

    def check(self, dep_file: FoundDepFile) -> CheckResult:
        key = _cache_key(dep_file)
        cached = self.cache.get(key)
        if cached is not None:
            self._cache_hits += 1
            return _deserialise_result(cached)

        self._cache_misses += 1
        result = check_dep_file(dep_file)
        self.cache.set(key, _serialise_result(result))
        return result

    @property
    def hit_rate(self) -> float:
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0
