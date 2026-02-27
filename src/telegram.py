"""Telegram trigger that routes incoming bot messages through the agent engine."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

@dataclass(frozen=True)
class TelegramMessage:
    """Normalized Telegram message payload consumed by the trigger."""

    update_id: int
    chat_id: int
    text: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process one Telegram update with the agent")
    parser.add_argument(
        "--bot-token",
        default=None,
        help="Telegram bot token (defaults to TELEGRAM_BOT_TOKEN env var)",
    )
    parser.add_argument("--system-message", required=True, help="System instruction text")
    parser.add_argument("--knowledge-base", required=True, help="Knowledge base context")
    parser.add_argument(
        "--offset",
        type=int,
        default=None,
        help="Telegram update offset. Use previous update_id + 1.",
    )
    parser.add_argument(
        "--poll-timeout",
        type=int,
        default=15,
        help="Long-poll timeout in seconds for getUpdates",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print agent output without sending a Telegram reply",
    )
    return parser


def resolve_bot_token(cli_token: str | None) -> str:
    token = (cli_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
    if not token:
        raise ValueError("bot token is required via --bot-token or TELEGRAM_BOT_TOKEN")
    return token


def telegram_api_call(token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    endpoint = f"https://api.telegram.org/bot{token}/{method}"
    request = Request(
        endpoint,
        data=urlencode(params).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Telegram API call failed for {method}") from exc

    if not payload.get("ok", False):
        description = payload.get("description", "unknown error")
        raise RuntimeError(f"Telegram API error for {method}: {description}")
    return payload


def get_updates(token: str, offset: int | None, timeout_seconds: int) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"timeout": timeout_seconds}
    if offset is not None:
        params["offset"] = offset
    payload = telegram_api_call(token, "getUpdates", params)
    results = payload.get("result")
    if not isinstance(results, list):
        raise RuntimeError("Telegram API returned non-list updates result")
    return results


def extract_latest_text_message(updates: list[dict[str, Any]]) -> TelegramMessage:
    for update in reversed(updates):
        update_id = update.get("update_id")
        message = update.get("message")
        if not isinstance(update_id, int) or not isinstance(message, dict):
            continue
        text = message.get("text")
        chat = message.get("chat")
        if not isinstance(text, str) or not text.strip():
            continue
        if not isinstance(chat, dict) or not isinstance(chat.get("id"), int):
            continue
        return TelegramMessage(
            update_id=update_id,
            chat_id=chat["id"],
            text=text.strip(),
        )

    raise ValueError("No text message found in Telegram updates payload")


def run_agent_reply(content: str, system_message: str, knowledge_base: str) -> str:
    cleaned_content = content.strip()
    cleaned_system = system_message.strip()
    cleaned_kb = knowledge_base.strip()
    if not cleaned_content:
        raise ValueError("content must be a non-empty string")
    if not cleaned_system:
        raise ValueError("system_message must be a non-empty string")
    if not cleaned_kb:
        raise ValueError("knowledge_base must be a non-empty string")
    return (
        f"System message: {cleaned_system}\n"
        f"Knowledge base: {cleaned_kb}\n"
        f"Output text: {cleaned_content}"
    )


def send_message(token: str, chat_id: int, text: str) -> None:
    telegram_api_call(token, "sendMessage", {"chat_id": chat_id, "text": text})


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.poll_timeout < 0:
        raise ValueError("poll-timeout must be >= 0")

    token = resolve_bot_token(args.bot_token)
    updates = get_updates(
        token=token,
        offset=args.offset,
        timeout_seconds=args.poll_timeout,
    )
    if not updates:
        print("No Telegram updates available.")
        return 0

    message = extract_latest_text_message(updates)
    response_text = run_agent_reply(
        content=message.text,
        system_message=args.system_message,
        knowledge_base=args.knowledge_base,
    )

    if args.dry_run:
        print(response_text)
    else:
        send_message(token, message.chat_id, response_text)
        print(f"Replied to chat_id={message.chat_id}")

    print(f"Next offset: {message.update_id + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
