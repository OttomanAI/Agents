from __future__ import annotations

import unittest

from commlinkio.core import JsonPathError, extract_json_path, extract_json_paths


class JsonExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = {
            "message": {
                "text": "hello",
                "entities": [{"type": "bold"}, {"type": "url", "url": "https://example.com"}],
            },
            "updates": [{"id": 10}, {"id": 20}, {"id": 30}],
            "meta.data": {"owner": {"id": "abc"}},
        }

    def test_extract_nested_field(self) -> None:
        self.assertEqual(extract_json_path(self.payload, "message.text"), ["hello"])

    def test_extract_array_index(self) -> None:
        self.assertEqual(extract_json_path(self.payload, "updates[1].id"), [20])

    def test_extract_array_negative_index(self) -> None:
        self.assertEqual(extract_json_path(self.payload, "updates[-1].id"), [30])

    def test_extract_array_wildcard(self) -> None:
        self.assertEqual(extract_json_path(self.payload, "updates[*].id"), [10, 20, 30])

    def test_extract_quoted_key(self) -> None:
        self.assertEqual(extract_json_path(self.payload, "['meta.data'].owner.id"), ["abc"])

    def test_extract_optional_root_prefix(self) -> None:
        self.assertEqual(extract_json_path(self.payload, "$.message.text"), ["hello"])

    def test_extract_missing_path_returns_empty_list(self) -> None:
        self.assertEqual(extract_json_path(self.payload, "message.caption"), [])

    def test_extract_json_paths_first_mode(self) -> None:
        results = extract_json_paths(self.payload, ["message.text", "message.caption"], first=True)
        self.assertEqual(results["message.text"], "hello")
        self.assertIsNone(results["message.caption"])

    def test_invalid_query_raises(self) -> None:
        with self.assertRaises(JsonPathError):
            extract_json_path(self.payload, "message..text")


if __name__ == "__main__":
    unittest.main()
