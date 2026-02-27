"""CLI tool for outbound Telegram typing/message actions."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from commlinkio.telegram.functions import send_text_message, send_typing_action


def _normalize_chat_id(value: str) -> int | str:
    if value.lstrip("-").isdigit():
        return int(value)
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="commlinkio-telegram-send",
        description="Send outbound Telegram actions or messages.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--token", help="Telegram bot token (defaults to TELEGRAM_BOT_TOKEN/.env).")
        subparser.add_argument("--compact", action="store_true", help="Print compact JSON output.")

    typing_parser = subparsers.add_parser("typing", help="Send typing action to a chat.")
    add_common_arguments(typing_parser)
    typing_parser.add_argument("--chat-id", required=True, help="Target chat id or @username.")

    message_parser = subparsers.add_parser("message", help="Send a text message to a chat.")
    add_common_arguments(message_parser)
    message_parser.add_argument("--chat-id", required=True, help="Target chat id or @username.")
    message_parser.add_argument("--text", required=True, help="Text to send.")
    message_parser.add_argument("--parse-mode", choices=["Markdown", "MarkdownV2", "HTML"])

    return parser


def _dump(payload: dict[str, Any], compact: bool) -> str:
    if compact:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    chat_id = _normalize_chat_id(args.chat_id)

    try:
        if args.command == "typing":
            ok = send_typing_action(chat_id, token=args.token)
            output: dict[str, Any] = {
                "command": "typing",
                "chat_id": chat_id,
                "ok": ok,
            }
        else:
            message = send_text_message(
                chat_id,
                args.text,
                token=args.token,
                parse_mode=args.parse_mode,
            )
            output = {
                "command": "message",
                "chat_id": chat_id,
                "message": message,
            }
    except Exception as exc:  # pragma: no cover - defensive CLI error handling
        print(str(exc), file=sys.stderr)
        return 2

    print(_dump(output, args.compact))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
