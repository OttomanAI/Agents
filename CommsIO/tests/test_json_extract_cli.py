from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from commlinkio.tools.json_extract import main


class JsonExtractCliTests(unittest.TestCase):
    def test_cli_prints_query_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "payload.json"
            json_path.write_text(
                json.dumps({"items": [{"id": 1}, {"id": 2}], "message": {"text": "ok"}}),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main([str(json_path), "-q", "items[*].id", "-q", "message.text"])

            self.assertEqual(code, 0)
            output = json.loads(stdout.getvalue())
            self.assertEqual(output["results"]["items[*].id"], [1, 2])
            self.assertEqual(output["results"]["message.text"], ["ok"])

    def test_cli_required_fails_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "payload.json"
            json_path.write_text(json.dumps({"message": {"text": "ok"}}), encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = main([str(json_path), "-q", "message.caption", "--required"])

            self.assertEqual(code, 2)
            self.assertIn("Missing required query matches", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
