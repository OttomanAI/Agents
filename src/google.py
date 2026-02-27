"""Helpers for Google/Gmail trigger payload handling."""

from __future__ import annotations

import base64
import json
from typing import Any


def extract_gmail_new_email_json(trigger_payload: dict[str, Any] | str) -> dict[str, str]:
    """Extract normalized email fields from a Gmail new-email trigger payload."""
    payload = _parse_trigger_payload(trigger_payload)
    message = payload.get("message")
    source = message if isinstance(message, dict) else payload

    headers = _extract_headers(source)
    body_text = _extract_body_text(source)

    normalized: dict[str, str] = {
        "message_id": _coalesce(
            source.get("id"),
            source.get("message_id"),
            source.get("messageId"),
        ),
        "thread_id": _coalesce(source.get("threadId"), source.get("thread_id")),
        "history_id": _coalesce(source.get("historyId"), source.get("history_id")),
        "subject": _coalesce(source.get("subject"), _header_value(headers, "subject")),
        "from": _coalesce(source.get("from"), _header_value(headers, "from")),
        "to": _coalesce(source.get("to"), _header_value(headers, "to")),
        "date": _coalesce(source.get("date"), _header_value(headers, "date")),
        "snippet": _coalesce(source.get("snippet"), source.get("bodyPreview"), body_text),
        "body_text": body_text,
    }
    return normalized


def _parse_trigger_payload(trigger_payload: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(trigger_payload, dict):
        return trigger_payload
    if isinstance(trigger_payload, str):
        cleaned = trigger_payload.strip()
        if not cleaned:
            raise ValueError("trigger_payload must be a non-empty JSON string")
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("trigger_payload is not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("trigger_payload JSON must be an object")
        return parsed
    raise ValueError("trigger_payload must be a dict or JSON string")


def _extract_headers(source: dict[str, Any]) -> dict[str, str]:
    payload_section = source.get("payload")
    if not isinstance(payload_section, dict):
        return {}
    raw_headers = payload_section.get("headers")
    if not isinstance(raw_headers, list):
        return {}

    headers: dict[str, str] = {}
    for item in raw_headers:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if isinstance(name, str) and isinstance(value, str):
            headers[name.lower()] = value.strip()
    return headers


def _header_value(headers: dict[str, str], key: str) -> str:
    return headers.get(key.lower(), "")


def _extract_body_text(source: dict[str, Any]) -> str:
    for key in ("body_text", "bodyPlain", "plainTextBody", "text", "body"):
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    payload_section = source.get("payload")
    if isinstance(payload_section, dict):
        decoded = _decode_body_from_payload(payload_section)
        if decoded:
            return decoded
    return ""


def _decode_body_from_payload(payload_section: dict[str, Any]) -> str:
    body = payload_section.get("body")
    if isinstance(body, dict):
        data = body.get("data")
        if isinstance(data, str) and data.strip():
            return _decode_base64url(data)

    parts = payload_section.get("parts")
    if isinstance(parts, list):
        for part in parts:
            if not isinstance(part, dict):
                continue
            mime_type = part.get("mimeType")
            part_body = part.get("body")
            if mime_type != "text/plain" or not isinstance(part_body, dict):
                continue
            data = part_body.get("data")
            if isinstance(data, str) and data.strip():
                decoded = _decode_base64url(data)
                if decoded:
                    return decoded
    return ""


def _decode_base64url(value: str) -> str:
    padded = value + "=" * ((4 - len(value) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
    except Exception:
        return ""
    return decoded.decode("utf-8", errors="ignore").strip()


def _coalesce(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""
