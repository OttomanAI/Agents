"""Basic Gmail trigger: wait for a new inbox email and return it as JSON."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

DEFAULT_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _load_google_dependencies() -> tuple[Any, Any, Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Install Gmail dependencies: pip install google-api-python-client google-auth-oauthlib"
        ) from exc
    return Request, Credentials, InstalledAppFlow, build


def _normalize_scopes(value: Any) -> list[str]:
    if value is None:
        return list(DEFAULT_SCOPES)
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def _build_service(credentials_file: Path, token_file: Path, scopes: list[str]) -> Any:
    Request, Credentials, InstalledAppFlow, build = _load_google_dependencies()

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes=scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_file.exists():
                raise FileNotFoundError(f"Gmail OAuth credentials file not found: {credentials_file}")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes)
            creds = flow.run_local_server(port=0)

        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _latest_message_id(service: Any, user_id: str, label_ids: list[str], query: str) -> str | None:
    params: dict[str, Any] = {"userId": user_id, "maxResults": 1}
    if label_ids:
        params["labelIds"] = label_ids
    if query:
        params["q"] = query

    result = service.users().messages().list(**params).execute()
    messages = result.get("messages") or []
    if not messages:
        return None
    return str(messages[0].get("id") or "") or None


def _decode_base64url(value: str) -> str:
    padded = value + "=" * ((4 - len(value) % 4) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
    except Exception:
        return ""
    return raw.decode("utf-8", errors="ignore").strip()


def _extract_headers(payload: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in payload.get("headers") or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if isinstance(name, str) and isinstance(value, str):
            output[name.lower()] = value.strip()
    return output


def _extract_body_text(payload: dict[str, Any]) -> str:
    body = payload.get("body")
    if isinstance(body, dict):
        data = body.get("data")
        if isinstance(data, str) and data:
            text = _decode_base64url(data)
            if text:
                return text

    for part in payload.get("parts") or []:
        if not isinstance(part, dict):
            continue
        text = _extract_body_text(part)
        if text:
            return text

    return ""


def _message_to_json(message: dict[str, Any]) -> dict[str, Any]:
    payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
    headers = _extract_headers(payload)
    return {
        "message_id": message.get("id", ""),
        "thread_id": message.get("threadId", ""),
        "history_id": message.get("historyId", ""),
        "internal_date": message.get("internalDate", ""),
        "label_ids": message.get("labelIds", []),
        "snippet": message.get("snippet", ""),
        "subject": headers.get("subject", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "date": headers.get("date", ""),
        "body_text": _extract_body_text(payload),
    }


class GmailWatchClient:
    """Poll inbox and return the first newly observed email as JSON."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def start_watch(self) -> dict[str, Any] | None:
        user_id = str(self.config.get("user_id", "me"))
        query = str(self.config.get("query", "in:inbox"))

        label_ids = self.config.get("label_ids", ["INBOX"])
        if isinstance(label_ids, str):
            label_ids = [part.strip() for part in label_ids.split(",") if part.strip()]
        if not isinstance(label_ids, list):
            label_ids = ["INBOX"]

        scopes = _normalize_scopes(self.config.get("scopes"))
        credentials_file = Path(
            self.config.get("credentials_file")
            or os.getenv("GMAIL_CREDENTIALS_FILE")
            or "credentials.json"
        ).expanduser()
        token_file = Path(
            self.config.get("token_file")
            or os.getenv("GMAIL_TOKEN_FILE")
            or "token.json"
        ).expanduser()

        include_existing = bool(self.config.get("include_existing", False))
        baseline_message_id = self.config.get("baseline_message_id")
        poll_interval = float(self.config.get("poll_interval_seconds", 5.0))
        timeout_seconds = float(self.config.get("timeout_seconds", 120.0))

        service = _build_service(credentials_file, token_file, scopes)

        if baseline_message_id is None and not include_existing:
            baseline_message_id = _latest_message_id(service, user_id, label_ids, query)

        deadline = time.time() + max(timeout_seconds, 0.0)
        while True:
            current_message_id = _latest_message_id(service, user_id, label_ids, query)
            is_new = current_message_id and (include_existing or current_message_id != baseline_message_id)
            if is_new:
                message = (
                    service.users()
                    .messages()
                    .get(userId=user_id, id=current_message_id, format="full")
                    .execute()
                )
                if isinstance(message, dict):
                    return _message_to_json(message)

            if timeout_seconds <= 0 or time.time() >= deadline:
                return None

            time.sleep(max(poll_interval, 0.5))


def gmail_inbox_watch_trigger(config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Run the Gmail trigger and return one email JSON payload or None on timeout."""
    return GmailWatchClient(config=config).start_watch()
