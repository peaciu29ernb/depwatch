"""Checks discovered dependency files for outdated or vulnerable packages."""

from __future__ import annotations

import subprocess
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from depwatch.scanner import FoundDepFile


@dataclass
class PackageIssue:
    name: str
    current_version: str
    latest_version: Optional[str] = None
    vulnerabilities: list[str] = field(default_factory=list)

    @property
    def is_outdated(self) -> bool:
        return self.latest_version is not None and self.current_version != self.latest_version

    @property
    def is_vulnerable(self) -> bool:
        return len(self.vulnerabilities) > 0


@dataclass
class CheckResult:
    dep_file: FoundDepFile
    issues: list[PackageIssue] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def outdated(self) -> list[PackageIssue]:
        return [i for i in self.issues if i.is_outdated]

    @property
    def vulnerable(self) -> list[PackageIssue]:
        return [i for i in self.issues if i.is_vulnerable]


def _check_pip(dep_file: FoundDepFile) -> CheckResult:
    """Run pip-audit against a requirements file."""
    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json", "-r", str(dep_file.path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        data = json.loads(result.stdout) if result.stdout else {}
        issues = []
        for dep in data.get("dependencies", []):
            vulns = [v["id"] for v in dep.get("vulns", [])]
            if vulns:
                issues.append(
                    PackageIssue(
                        name=dep["name"],
                        current_version=dep["version"],
                        vulnerabilities=vulns,
                    )
                )
        return CheckResult(dep_file=dep_file, issues=issues)
    except FileNotFoundError:
        return CheckResult(dep_file=dep_file, error="pip-audit not found")
    except Exception as exc:  # noqa: BLE001
        return CheckResult(dep_file=dep_file, error=str(exc))


_CHECKERS = {
    "pip": _check_pip,
}


def check_dep_file(dep_file: FoundDepFile) -> CheckResult:
    """Dispatch to the appropriate checker based on ecosystem."""
    checker = _CHECKERS.get(dep_file.ecosystem)
    if checker is None:
        return CheckResult(
            dep_file=dep_file,
            error=f"No checker available for ecosystem '{dep_file.ecosystem}'",
        )
    return checker(dep_file)
