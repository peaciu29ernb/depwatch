"""Dependency file parsers for various ecosystems."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ParsedPackage:
    name: str
    version: Optional[str] = None
    extras: List[str] = field(default_factory=list)


@dataclass
class ParseResult:
    ecosystem: str
    packages: List[ParsedPackage] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _parse_requirements_txt(path: Path) -> ParseResult:
    packages: List[ParsedPackage] = []
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Strip inline comments
            line = line.split("#")[0].strip()
            match = re.match(
                r"^([A-Za-z0-9_.-]+)(\[.*?\])?\s*(?:[=<>!~]+\s*([^,\s]+))?", line
            )
            if match:
                name = match.group(1)
                extras_raw = match.group(2) or ""
                version = match.group(3)
                extras = [e.strip() for e in extras_raw.strip("[]").split(",") if e.strip()]
                packages.append(ParsedPackage(name=name, version=version, extras=extras))
    except OSError as exc:
        return ParseResult(ecosystem="pip", error=str(exc))
    return ParseResult(ecosystem="pip", packages=packages)


def _parse_package_json(path: Path) -> ParseResult:
    packages: List[ParsedPackage] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ParseResult(ecosystem="npm", error=str(exc))
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        for name, version in data.get(section, {}).items():
            packages.append(ParsedPackage(name=name, version=version.lstrip("^~") or None))
    return ParseResult(ecosystem="npm", packages=packages)


_PARSERS = {
    "requirements.txt": _parse_requirements_txt,
    "package.json": _parse_package_json,
}


def parse_dep_file(path: Path) -> ParseResult:
    """Parse a dependency file and return a ParseResult."""
    parser = _PARSERS.get(path.name)
    if parser is None:
        return ParseResult(ecosystem="unknown", error=f"No parser for '{path.name}'")
    return parser(path)
