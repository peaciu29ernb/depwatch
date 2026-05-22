"""Configuration loader for depwatch daemon."""

import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class RepoConfig:
    path: str
    name: Optional[str] = None
    enabled: bool = True

    def __post_init__(self):
        if self.name is None:
            self.name = os.path.basename(self.path.rstrip("/"))


@dataclass
class DepwatchConfig:
    repos: List[RepoConfig] = field(default_factory=list)
    check_interval: int = 3600  # seconds
    alert_email: Optional[str] = None
    vulnerability_check: bool = True
    outdated_check: bool = True
    log_level: str = "INFO"


def load_config(config_path: str) -> DepwatchConfig:
    """Load and parse the depwatch YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError("Config file must be a YAML mapping")

    repos = [
        RepoConfig(
            path=r["path"],
            name=r.get("name"),
            enabled=r.get("enabled", True),
        )
        for r in raw.get("repos", [])
    ]

    return DepwatchConfig(
        repos=repos,
        check_interval=raw.get("check_interval", 3600),
        alert_email=raw.get("alert_email"),
        vulnerability_check=raw.get("vulnerability_check", True),
        outdated_check=raw.get("outdated_check", True),
        log_level=raw.get("log_level", "INFO"),
    )
