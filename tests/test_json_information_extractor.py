from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "json_information_extractor.py"
SPEC = importlib.util.spec_from_file_location("json_information_extractor", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_extract_json_value_reads_nested_path() -> None:
    payload = {"message": {"payload": {"headers": [{"value": "Hello"}]}}}
    value = MODULE.extract_json_value(payload, "message.payload.headers[0].value")
    assert value == "Hello"


def test_extract_json_value_handles_list_dot_index() -> None:
    payload = {"matches": [{"metadata": {"text": "chunk a"}}, {"metadata": {"text": "chunk b"}}]}
    value = MODULE.extract_json_value(payload, "matches[1].metadata.text")
    assert value == "chunk b"


def test_extract_json_value_returns_default_when_missing() -> None:
    payload = {"message": {"id": "abc"}}
    value = MODULE.extract_json_value(payload, "message.subject", default="(none)")
    assert value == "(none)"


def test_extract_json_value_raises_when_strict_and_missing() -> None:
    payload = {"message": {"id": "abc"}}
    try:
        MODULE.extract_json_value(payload, "message.subject", strict=True)
        assert False, "Expected ValueError for missing path in strict mode"
    except ValueError as exc:
        assert "Path not found" in str(exc)


def test_parse_json_path_rejects_invalid_path() -> None:
    try:
        MODULE.parse_json_path("matches[abc].metadata")
        assert False, "Expected ValueError for invalid index token"
    except ValueError as exc:
        assert "Invalid list index" in str(exc)
