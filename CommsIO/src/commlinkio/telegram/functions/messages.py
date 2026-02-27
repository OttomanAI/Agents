"""Telegram outbound message functions."""

from __future__ import annotations

from typing import Any

from commlinkio.telegram.clients import TelegramBotClient


async def send_text_message_async(
    chat_id: int | str,
    text: str,
    *,
    token: str | None = None,
    parse_mode: str | None = None,
    client: TelegramBotClient | None = None,
) -> dict[str, Any]:
    """Send a text message to a Telegram chat (async)."""

    active_client = client or TelegramBotClient(token=token)
    return await active_client.send_message_async(chat_id, text, parse_mode=parse_mode)


def send_text_message(
    chat_id: int | str,
    text: str,
    *,
    token: str | None = None,
    parse_mode: str | None = None,
    client: TelegramBotClient | None = None,
) -> dict[str, Any]:
    """Send a text message to a Telegram chat."""

    active_client = client or TelegramBotClient(token=token)
    return active_client.send_message(chat_id, text, parse_mode=parse_mode)
