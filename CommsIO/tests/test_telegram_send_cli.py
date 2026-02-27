from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from commlinkio.telegram.tools.send import main


class TelegramSendCliTests(unittest.TestCase):
    def test_typing_command(self) -> None:
        with patch("commlinkio.telegram.tools.send.send_typing_action", return_value=True) as mock_send:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["typing", "--chat-id", "123"])

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["command"], "typing")
        self.assertTrue(payload["ok"])
        mock_send.assert_called_once_with(123, token=None)

    def test_message_command(self) -> None:
        response = {"message_id": 1, "text": "hello"}
        with patch("commlinkio.telegram.tools.send.send_text_message", return_value=response) as mock_send:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "message",
                        "--chat-id",
                        "@my_channel",
                        "--text",
                        "hello",
                        "--parse-mode",
                        "HTML",
                    ]
                )

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["command"], "message")
        self.assertEqual(payload["message"]["message_id"], 1)
        mock_send.assert_called_once_with("@my_channel", "hello", token=None, parse_mode="HTML")

    def test_command_errors_return_non_zero(self) -> None:
        with patch("commlinkio.telegram.tools.send.send_typing_action", side_effect=ValueError("boom")):
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = main(["typing", "--chat-id", "123"])

        self.assertEqual(code, 2)
        self.assertIn("boom", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
