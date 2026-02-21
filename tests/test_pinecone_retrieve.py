from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "pinecone" / "retrieve.py"
SPEC = importlib.util.spec_from_file_location("pinecone_retrieve", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_parse_vector_accepts_numeric_json_array() -> None:
    vector = MODULE._parse_vector("[1, 2.5, 3]")
    assert vector == [1.0, 2.5, 3.0]


def test_parse_filter_returns_dict() -> None:
    payload = MODULE._parse_filter('{"tenant_id": "acme"}')
    assert payload == {"tenant_id": "acme"}


def test_normalize_matches_uses_fallback_text_key() -> None:
    raw = {
        "matches": [
            {
                "id": "chunk-1",
                "score": 0.92,
                "metadata": {"chunk_text": "retrieved context"},
            }
        ]
    }

    matches = MODULE._normalize_matches(raw, text_key="text")

    assert len(matches) == 1
    assert matches[0].match_id == "chunk-1"
    assert matches[0].score == 0.92
    assert matches[0].text == "retrieved context"
