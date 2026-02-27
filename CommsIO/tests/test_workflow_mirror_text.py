"""Workflow test 1.

Listens for Telegram updates, extracts fields from update JSON, sends typing action,
waits 2 seconds, and replies with the same text that was sent to the bot.
"""

from __future__ import annotations

import asyncio
from typing import Any

from commlinkio.core import extract_json_paths
from commlinkio.telegram.functions import send_text_message_async, send_typing_action_async
from commlinkio.telegram.readers import TelegramUpdateReader
from commlinkio.telegram.triggers.updates_trigger import TelegramUpdatesTrigger

# Keep an explicit import reference to the existing trigger module.
_BASE_TRIGGER = TelegramUpdatesTrigger


class Workflow1EchoTrigger:
    """Echo workflow: typing -> delay -> reply with original text."""

    def __init__(self, token: str | None = None, delay_seconds: float = 2.0):
        self._token = token
        self._delay_seconds = delay_seconds
        self._reader = TelegramUpdateReader(token=token, on_update=self._handle_update)

    async def _handle_update(self, payload: dict[str, Any]) -> None:
        extracted = extract_json_paths(
            payload,
            [
                "chat.id",
                "message.chat.id",
                "text",
                "message.text",
            ],
            first=True,
        )

        chat_id = (
            extracted["chat.id"]
            if extracted["chat.id"] is not None
            else extracted["message.chat.id"]
        )
        text = extracted["text"] if extracted["text"] else extracted["message.text"]

        if chat_id is None or text is None:
            return

        await send_typing_action_async(chat_id, token=self._token)
        await asyncio.sleep(self._delay_seconds)
        await send_text_message_async(chat_id, str(text), token=self._token)

    def start(self) -> None:
        """Run the workflow (blocking)."""

        self._reader.start()


def main() -> None:
    Workflow1EchoTrigger().start()


if __name__ == "__main__":
    main()
