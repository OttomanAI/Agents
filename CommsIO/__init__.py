"""Importable communication helpers package."""

from __future__ import annotations

from . import telegram
from .gmail import GmailWatchClient, gmail_inbox_watch_trigger
from .telegram import (
    telegram_get_updates,
    telegram_message_trigger,
    telegram_send_message,
    telegram_send_typing,
    telegram_updates_trigger,
    trigger,
)

__all__ = [
    "telegram",
    "GmailWatchClient",
    "gmail_inbox_watch_trigger",
    "trigger",
    "telegram_get_updates",
    "telegram_message_trigger",
    "telegram_updates_trigger",
    "telegram_send_message",
    "telegram_send_typing",
]
