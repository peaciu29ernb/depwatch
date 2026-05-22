"""Notification backends package."""

from depwatch.backends.slack import SlackBackend
from depwatch.backends.webhook import WebhookBackend

__all__ = ["SlackBackend", "WebhookBackend"]
