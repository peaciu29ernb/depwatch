"""Scans repository paths for known dependency files."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Mapping of dependency file names to their ecosystem
DEP_FILE_ECOSYSTEMS: dict[str, str] = {
    "requirements.txt": "pip",
    "requirements.in": "pip",
    "Pipfile": "pipenv",
    "Pipfile.lock": "pipenv",
    "pyproject.toml": "python",
    "setup.cfg": "python",
    "package.json": "npm",
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
    "Gemfile": "rubygems",
    "Gemfile.lock": "rubygems",
    "go.mod": "go",
    "go.sum": "go",
    "Cargo.toml": "cargo",
    "Cargo.lock": "cargo",
}


@dataclass
class FoundDepFile:
    """Represents a discovered dependency file."""

    path: Path
    ecosystem: str

    @property
    def filename(self) -> str:
        return self.path.name


@dataclass
class ScanResult:
    """Result of scanning a single repository path."""

    repo_path: Path
    dep_files: List[FoundDepFile] = field(default_factory=list)

    @property
    def ecosystems(self) -> List[str]:
        return list({f.ecosystem for f in self.dep_files})


def scan_repo(repo_path: str | Path, max_depth: int = 3) -> ScanResult:
    """Walk *repo_path* up to *max_depth* levels deep and collect dependency files."""
    root = Path(repo_path).resolve()
    result = ScanResult(repo_path=root)

    if not root.is_dir():
        raise NotADirectoryError(f"repo_path is not a directory: {root}")

    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        depth = len(current.relative_to(root).parts)
        if depth >= max_depth:
            dirnames.clear()  # prune further recursion
            continue
        # Skip hidden directories (e.g. .git, .tox)
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        for filename in filenames:
            ecosystem = DEP_FILE_ECOSYSTEMS.get(filename)
            if ecosystem:
                result.dep_files.append(
                    FoundDepFile(path=current / filename, ecosystem=ecosystem)
                )

    return result
