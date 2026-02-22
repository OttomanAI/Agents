from telegram import TelegramMessage, extract_latest_text_message, resolve_bot_token


def test_extract_latest_text_message_returns_latest_text() -> None:
    updates = [
        {"update_id": 10, "message": {"chat": {"id": 1}, "text": "First"}},
        {"update_id": 11, "message": {"chat": {"id": 2}, "text": "Second"}},
    ]

    message = extract_latest_text_message(updates)

    assert message == TelegramMessage(update_id=11, chat_id=2, text="Second")


def test_extract_latest_text_message_skips_non_text_messages() -> None:
    updates = [
        {"update_id": 12, "message": {"chat": {"id": 1}, "sticker": {"emoji": "👍"}}},
        {"update_id": 13, "message": {"chat": {"id": 3}, "text": "  Hello  "}},
    ]

    message = extract_latest_text_message(updates)

    assert message == TelegramMessage(update_id=13, chat_id=3, text="Hello")


def test_extract_latest_text_message_raises_when_no_text() -> None:
    updates = [{"update_id": 14, "message": {"chat": {"id": 4}, "photo": []}}]

    try:
        extract_latest_text_message(updates)
        assert False, "Expected ValueError when there is no text message"
    except ValueError as exc:
        assert "No text message found" in str(exc)


def test_resolve_bot_token_uses_cli_value() -> None:
    token = resolve_bot_token("abc123")
    assert token == "abc123"
