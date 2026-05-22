"""Slack notification backend."""

from dataclasses import dataclass
from typing import Any, Dict
import urllib.request
import json


@dataclass
class SlackBackend:
    """Posts a message to a Slack incoming webhook URL."""

    webhook_url: str
    username: str = "depwatch"
    icon_emoji: str = ":shield:"
    timeout: int = 10

    def send(self, subject: str, body: str) -> None:
        text = subject
        if body:
            text = f"*{subject}*\n```{body}```"

        payload: Dict[str, Any] = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "text": text,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            if resp.status not in (200, 201, 204):
                raise RuntimeError(
                    f"Slack webhook returned HTTP {resp.status}"
                )
