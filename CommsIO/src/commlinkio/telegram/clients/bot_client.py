"""Telegram bot client for outbound actions/messages."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ChatAction


ChatId = int | str


class TelegramBotClient:
    """Thin client around python-telegram-bot's Bot for outbound operations."""

    def __init__(self, token: str | None = None):
        load_dotenv()
        resolved_token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not resolved_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required.")
        self._bot = Bot(token=resolved_token)

    async def send_typing_async(self, chat_id: ChatId) -> bool:
        """Send the typing action to a Telegram chat."""

        return await self._bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    async def send_message_async(
        self,
        chat_id: ChatId,
        text: str,
        *,
        parse_mode: str | None = None,
    ) -> dict[str, Any]:
        """Send a text message and return the Telegram API response as a dict."""

        message = await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
        )
        return message.to_dict(recursive=True)

    def send_typing(self, chat_id: ChatId) -> bool:
        """Sync wrapper for send_typing_async."""

        return self._run_sync(self.send_typing_async(chat_id))

    def send_message(
        self,
        chat_id: ChatId,
        text: str,
        *,
        parse_mode: str | None = None,
    ) -> dict[str, Any]:
        """Sync wrapper for send_message_async."""

        return self._run_sync(self.send_message_async(chat_id, text, parse_mode=parse_mode))

    @staticmethod
    def _run_sync(coro: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        raise RuntimeError("Cannot call sync method from a running event loop. Use async methods instead.")
