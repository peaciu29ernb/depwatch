"""Simple file-based cache for check results to avoid redundant API calls."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CacheEntry:
    key: str
    value: dict
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 3600

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return self.hits / self.total if self.total > 0 else 0.0


class ResultCache:
    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600) -> None:
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.stats = CacheStats()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def get(self, key: str) -> Optional[dict]:
        path = self._key_path(key)
        if not path.exists():
            self.stats.misses += 1
            return None
        try:
            entry_data = json.loads(path.read_text())
            entry = CacheEntry(**entry_data)
            if entry.is_expired():
                path.unlink(missing_ok=True)
                self.stats.evictions += 1
                self.stats.misses += 1
                return None
            self.stats.hits += 1
            return entry.value
        except (json.JSONDecodeError, TypeError):
            path.unlink(missing_ok=True)
            self.stats.misses += 1
            return None

    def set(self, key: str, value: dict) -> None:
        entry = CacheEntry(key=key, value=value, ttl_seconds=self.ttl_seconds)
        path = self._key_path(key)
        path.write_text(json.dumps(entry.__dict__))

    def invalidate(self, key: str) -> bool:
        path = self._key_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        removed = 0
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
            removed += 1
        return removed
