import base64
import json

from google import extract_gmail_new_email_json


def test_extract_gmail_new_email_json_from_dict_payload() -> None:
    trigger_payload = {
        "message": {
            "id": "18f8f71",
            "threadId": "18f8f11",
            "historyId": "1024",
            "snippet": "Status update attached",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Weekly Report"},
                    {"name": "From", "value": "ops@example.com"},
                    {"name": "To", "value": "team@example.com"},
                    {"name": "Date", "value": "Mon, 01 Jan 2026 10:00:00 +0000"},
                ]
            },
        }
    }

    extracted = extract_gmail_new_email_json(trigger_payload)

    assert extracted["message_id"] == "18f8f71"
    assert extracted["thread_id"] == "18f8f11"
    assert extracted["history_id"] == "1024"
    assert extracted["subject"] == "Weekly Report"
    assert extracted["from"] == "ops@example.com"
    assert extracted["to"] == "team@example.com"
    assert extracted["snippet"] == "Status update attached"


def test_extract_gmail_new_email_json_from_json_string_with_encoded_body() -> None:
    encoded_body = base64.urlsafe_b64encode(b"Hello from Gmail trigger").decode("utf-8").rstrip("=")
    trigger_payload = json.dumps(
        {
            "id": "18f8f72",
            "threadId": "18f8f12",
            "payload": {
                "headers": [{"name": "Subject", "value": "Hello"}],
                "body": {"data": encoded_body},
            },
        }
    )

    extracted = extract_gmail_new_email_json(trigger_payload)

    assert extracted["message_id"] == "18f8f72"
    assert extracted["thread_id"] == "18f8f12"
    assert extracted["subject"] == "Hello"
    assert extracted["body_text"] == "Hello from Gmail trigger"
    assert extracted["snippet"] == "Hello from Gmail trigger"


def test_extract_gmail_new_email_json_rejects_invalid_payload() -> None:
    try:
        extract_gmail_new_email_json("not-json")
        assert False, "Expected ValueError for invalid JSON input"
    except ValueError as exc:
        assert "valid JSON" in str(exc)
