"""Tests for depwatch.cache module."""
import json
import time
from pathlib import Path

import pytest

from depwatch.cache import CacheEntry, CacheStats, ResultCache


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    return tmp_path / "cache"


@pytest.fixture
def cache(cache_dir: Path) -> ResultCache:
    return ResultCache(cache_dir, ttl_seconds=60)


def test_cache_dir_created_on_init(cache_dir: Path) -> None:
    ResultCache(cache_dir)
    assert cache_dir.is_dir()


def test_get_returns_none_for_missing_key(cache: ResultCache) -> None:
    assert cache.get("nonexistent") is None


def test_set_and_get_roundtrip(cache: ResultCache) -> None:
    cache.set("pkg:requests:2.28", {"latest": "2.31", "vulnerable": False})
    result = cache.get("pkg:requests:2.28")
    assert result == {"latest": "2.31", "vulnerable": False}


def test_get_returns_none_for_expired_entry(cache_dir: Path) -> None:
    c = ResultCache(cache_dir, ttl_seconds=1)
    c.set("key", {"data": "value"})
    # Manually expire by rewriting with old timestamp
    digest_path = list(cache_dir.glob("*.json"))[0]
    entry_data = json.loads(digest_path.read_text())
    entry_data["created_at"] = time.time() - 3600
    digest_path.write_text(json.dumps(entry_data))
    assert c.get("key") is None


def test_expired_entry_increments_eviction(cache_dir: Path) -> None:
    c = ResultCache(cache_dir, ttl_seconds=1)
    c.set("key", {})
    digest_path = list(cache_dir.glob("*.json"))[0]
    entry_data = json.loads(digest_path.read_text())
    entry_data["created_at"] = time.time() - 3600
    digest_path.write_text(json.dumps(entry_data))
    c.get("key")
    assert c.stats.evictions == 1


def test_stats_hits_and_misses(cache: ResultCache) -> None:
    cache.set("k", {"v": 1})
    cache.get("k")   # hit
    cache.get("x")   # miss
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1


def test_stats_hit_rate(cache: ResultCache) -> None:
    cache.set("k", {})
    cache.get("k")
    cache.get("k")
    cache.get("missing")
    assert abs(cache.stats.hit_rate - 2 / 3) < 1e-9


def test_invalidate_removes_entry(cache: ResultCache) -> None:
    cache.set("key", {"x": 1})
    removed = cache.invalidate("key")
    assert removed is True
    assert cache.get("key") is None


def test_invalidate_returns_false_for_missing(cache: ResultCache) -> None:
    assert cache.invalidate("nope") is False


def test_clear_removes_all_entries(cache: ResultCache) -> None:
    cache.set("a", {})
    cache.set("b", {})
    cache.set("c", {})
    removed = cache.clear()
    assert removed == 3
    assert cache.get("a") is None


def test_cache_entry_not_expired_when_fresh() -> None:
    entry = CacheEntry(key="k", value={}, ttl_seconds=3600)
    assert not entry.is_expired()


def test_cache_entry_expired_when_old() -> None:
    entry = CacheEntry(key="k", value={}, created_at=time.time() - 7200, ttl_seconds=3600)
    assert entry.is_expired()


def test_get_handles_corrupt_cache_file(cache: ResultCache, cache_dir: Path) -> None:
    cache.set("key", {"v": 1})
    for f in cache_dir.glob("*.json"):
        f.write_text("not valid json{{")
    assert cache.get("key") is None
