"""Telegram outbound action functions."""

from __future__ import annotations

from commlinkio.telegram.clients import TelegramBotClient


async def send_typing_action_async(
    chat_id: int | str,
    *,
    token: str | None = None,
    client: TelegramBotClient | None = None,
) -> bool:
    """Send the typing action to a Telegram chat (async)."""

    active_client = client or TelegramBotClient(token=token)
    return await active_client.send_typing_async(chat_id)


def send_typing_action(
    chat_id: int | str,
    *,
    token: str | None = None,
    client: TelegramBotClient | None = None,
) -> bool:
    """Send the typing action to a Telegram chat."""

    active_client = client or TelegramBotClient(token=token)
    return active_client.send_typing(chat_id)
