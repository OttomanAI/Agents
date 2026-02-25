"""Basic Telegram trigger and send helpers."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MESSAGE_KEYS = ("message", "edited_message", "channel_post", "edited_channel_post")


def _resolve_token(config: dict[str, Any] | None = None) -> str:
    cfg = config or {}
    token = str(cfg.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise ValueError("Telegram bot token missing. Set TELEGRAM_BOT_TOKEN or pass config['bot_token'].")
    return token


def _api_call(token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    request = Request(
        url,
        data=urlencode(params).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Telegram API request failed for {method}") from exc

    if not payload.get("ok", False):
        raise RuntimeError(f"Telegram API error for {method}: {payload.get('description', 'unknown error')}")
    result = payload.get("result")
    return result if isinstance(result, dict) else {"result": result}


def telegram_get_updates(config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    cfg = config or {}
    token = _resolve_token(cfg)

    params: dict[str, Any] = {"timeout": int(cfg.get("poll_timeout_seconds", 15))}
    if "offset" in cfg and cfg["offset"] is not None:
        params["offset"] = int(cfg["offset"])
    if "allowed_updates" in cfg and cfg["allowed_updates"] is not None:
        params["allowed_updates"] = json.dumps(cfg["allowed_updates"])

    result = _api_call(token, "getUpdates", params)
    updates = result.get("result")
    return updates if isinstance(updates, list) else []


def _latest_update_id(updates: list[dict[str, Any]]) -> int | None:
    ids = [u.get("update_id") for u in updates if isinstance(u.get("update_id"), int)]
    return max(ids) if ids else None


def _normalize_message_update(update: dict[str, Any]) -> dict[str, Any] | None:
    message_key = None
    message = None
    for key in MESSAGE_KEYS:
        candidate = update.get(key)
        if isinstance(candidate, dict):
            message_key = key
            message = candidate
            break

    if message is None or message_key is None:
        return None

    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    sender = message.get("from") if isinstance(message.get("from"), dict) else {}
    text = message.get("text") or message.get("caption") or ""

    return {
        "update_id": update.get("update_id"),
        "message_type": message_key,
        "message_id": message.get("message_id"),
        "date": message.get("date"),
        "text": text if isinstance(text, str) else "",
        "chat": {
            "id": chat.get("id"),
            "type": chat.get("type"),
            "title": chat.get("title"),
            "username": chat.get("username"),
            "first_name": chat.get("first_name"),
            "last_name": chat.get("last_name"),
        },
        "sender": {
            "id": sender.get("id"),
            "is_bot": sender.get("is_bot"),
            "username": sender.get("username"),
            "first_name": sender.get("first_name"),
            "last_name": sender.get("last_name"),
            "language_code": sender.get("language_code"),
        },
        "entities": message.get("entities", []),
        "raw": update,
    }


def _latest_message_json(updates: list[dict[str, Any]], baseline_update_id: int | None = None) -> dict[str, Any] | None:
    for update in reversed(updates):
        if not isinstance(update, dict):
            continue

        update_id = update.get("update_id")
        if baseline_update_id is not None:
            if not isinstance(update_id, int) or update_id <= baseline_update_id:
                continue

        normalized = _normalize_message_update(update)
        if normalized is not None:
            return normalized

    return None


def trigger(config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Wait for the latest new message and return normalized JSON payload."""
    cfg = config or {}

    include_existing = bool(cfg.get("include_existing", False))
    baseline_update_id_value = cfg.get("baseline_update_id")
    baseline_update_id = int(baseline_update_id_value) if baseline_update_id_value is not None else None
    poll_interval = float(cfg.get("poll_interval_seconds", 2.0))
    timeout_seconds = float(cfg.get("timeout_seconds", 120.0))

    if baseline_update_id is None and not include_existing:
        baseline = telegram_get_updates({**cfg, "poll_timeout_seconds": 0})
        baseline_update_id = _latest_update_id(baseline)

    deadline = time.time() + max(timeout_seconds, 0.0)
    while True:
        updates = telegram_get_updates({**cfg, "poll_timeout_seconds": 15})
        if updates:
            normalized = _latest_message_json(
                updates,
                None if include_existing else baseline_update_id,
            )
            if normalized is not None:
                return normalized

        if timeout_seconds <= 0 or time.time() >= deadline:
            return None

        time.sleep(max(poll_interval, 0.5))


def telegram_message_trigger(config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Backward-compatible alias for `trigger`."""
    return trigger(config=config)


def telegram_updates_trigger(config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Backward-compatible alias for `trigger`."""
    return trigger(config=config)


def telegram_send_message(text: str, chat_id: int, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or {}
    token = _resolve_token(cfg)
    params: dict[str, Any] = {"chat_id": int(chat_id), "text": str(text)}
    if "parse_mode" in cfg and cfg["parse_mode"]:
        params["parse_mode"] = str(cfg["parse_mode"])
    return _api_call(token, "sendMessage", params)


def telegram_send_typing(chat_id: int, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or {}
    token = _resolve_token(cfg)
    return _api_call(token, "sendChatAction", {"chat_id": int(chat_id), "action": "typing"})
