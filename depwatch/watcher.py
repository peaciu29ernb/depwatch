"""File system watcher that detects changes to dependency files."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from depwatch.scanner import FoundDepFile


@dataclass
class FileSnapshot:
    path: str
    mtime: float
    checksum: str


@dataclass
class WatcherState:
    snapshots: Dict[str, FileSnapshot] = field(default_factory=dict)

    def update(self, snapshot: FileSnapshot) -> None:
        self.snapshots[snapshot.path] = snapshot

    def get(self, path: str) -> Optional[FileSnapshot]:
        return self.snapshots.get(path)


@dataclass
class ChangeSet:
    added: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.removed)


def _checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot(path: str) -> Optional[FileSnapshot]:
    try:
        stat = os.stat(path)
        return FileSnapshot(path=path, mtime=stat.st_mtime, checksum=_checksum(path))
    except OSError:
        return None


def detect_changes(
    dep_files: List[FoundDepFile],
    state: WatcherState,
) -> ChangeSet:
    """Compare current dep files against stored state and return a ChangeSet."""
    changeset = ChangeSet()
    current_paths = {df.path for df in dep_files}

    for dep_file in dep_files:
        snap = _snapshot(dep_file.path)
        if snap is None:
            continue
        prev = state.get(dep_file.path)
        if prev is None:
            changeset.added.append(dep_file.path)
        elif prev.checksum != snap.checksum:
            changeset.modified.append(dep_file.path)
        state.update(snap)

    for known_path in list(state.snapshots):
        if known_path not in current_paths:
            changeset.removed.append(known_path)
            del state.snapshots[known_path]

    return changeset
