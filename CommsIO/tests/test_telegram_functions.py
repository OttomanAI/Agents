from __future__ import annotations

import asyncio
import unittest

from commlinkio.telegram.functions import (
    send_text_message,
    send_text_message_async,
    send_typing_action,
    send_typing_action_async,
)


class _FakeTelegramClient:
    def __init__(self) -> None:
        self.typing_calls: list[int | str] = []
        self.message_calls: list[tuple[int | str, str, str | None]] = []
        self.typing_async_calls: list[int | str] = []
        self.message_async_calls: list[tuple[int | str, str, str | None]] = []

    def send_typing(self, chat_id: int | str) -> bool:
        self.typing_calls.append(chat_id)
        return True

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        parse_mode: str | None = None,
    ) -> dict[str, object]:
        self.message_calls.append((chat_id, text, parse_mode))
        return {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}

    async def send_typing_async(self, chat_id: int | str) -> bool:
        self.typing_async_calls.append(chat_id)
        return True

    async def send_message_async(
        self,
        chat_id: int | str,
        text: str,
        *,
        parse_mode: str | None = None,
    ) -> dict[str, object]:
        self.message_async_calls.append((chat_id, text, parse_mode))
        return {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}


class TelegramFunctionsTests(unittest.TestCase):
    def test_send_typing_action_uses_client(self) -> None:
        client = _FakeTelegramClient()
        ok = send_typing_action(12345, client=client)  # type: ignore[arg-type]
        self.assertTrue(ok)
        self.assertEqual(client.typing_calls, [12345])

    def test_send_text_message_uses_client(self) -> None:
        client = _FakeTelegramClient()
        result = send_text_message(777, "Hello", parse_mode="HTML", client=client)  # type: ignore[arg-type]
        self.assertEqual(client.message_calls, [(777, "Hello", "HTML")])
        self.assertEqual(result["text"], "Hello")

    def test_send_typing_action_async_uses_client(self) -> None:
        client = _FakeTelegramClient()
        ok = asyncio.run(send_typing_action_async(12345, client=client))  # type: ignore[arg-type]
        self.assertTrue(ok)
        self.assertEqual(client.typing_async_calls, [12345])

    def test_send_text_message_async_uses_client(self) -> None:
        client = _FakeTelegramClient()
        result = asyncio.run(send_text_message_async(777, "Hello", parse_mode="HTML", client=client))  # type: ignore[arg-type]
        self.assertEqual(client.message_async_calls, [(777, "Hello", "HTML")])
        self.assertEqual(result["text"], "Hello")


if __name__ == "__main__":
    unittest.main()
