"""Generic JSON extraction utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


class JsonPathError(ValueError):
    """Raised when a JSON query path is invalid."""


TokenType = Literal["field", "index", "wildcard"]


@dataclass(frozen=True)
class _PathToken:
    kind: TokenType
    value: str | int | None = None


def _parse_bracket(query: str, start: int) -> tuple[_PathToken, int]:
    i = start + 1
    if i >= len(query):
        raise JsonPathError("Unterminated bracket expression.")

    if query[i] == "*":
        if i + 1 >= len(query) or query[i + 1] != "]":
            raise JsonPathError("Wildcard bracket must be [*].")
        return _PathToken("wildcard"), i + 2

    if query[i] in ("'", '"'):
        quote = query[i]
        i += 1
        chars: list[str] = []
        while i < len(query):
            char = query[i]
            if char == "\\":
                i += 1
                if i >= len(query):
                    raise JsonPathError("Invalid escape in bracket key.")
                chars.append(query[i])
            elif char == quote:
                i += 1
                if i >= len(query) or query[i] != "]":
                    raise JsonPathError("Quoted bracket key must end with ].")
                return _PathToken("field", "".join(chars)), i + 1
            else:
                chars.append(char)
            i += 1
        raise JsonPathError("Unterminated quoted bracket key.")

    j = i
    if query[j] == "-":
        j += 1
    if j >= len(query) or not query[j].isdigit():
        raise JsonPathError("Bracket expression must be an index, wildcard, or quoted key.")
    while j < len(query) and query[j].isdigit():
        j += 1
    if j >= len(query) or query[j] != "]":
        raise JsonPathError("Array index bracket must end with ].")
    return _PathToken("index", int(query[i:j])), j + 1


def _parse_query(query: str) -> list[_PathToken]:
    raw = query.strip()
    if not raw:
        raise JsonPathError("Query cannot be empty.")

    if raw.startswith("$"):
        raw = raw[1:]
        if raw.startswith("."):
            raw = raw[1:]

    if not raw:
        return []

    tokens: list[_PathToken] = []
    i = 0

    while i < len(raw):
        char = raw[i]

        if char == ".":
            if i == 0 or i + 1 >= len(raw) or raw[i + 1] == ".":
                raise JsonPathError("Invalid '.' placement in query.")
            i += 1
            continue

        if char == "[":
            token, i = _parse_bracket(raw, i)
            tokens.append(token)
            continue

        if char == "*":
            tokens.append(_PathToken("wildcard"))
            i += 1
            continue

        start = i
        while i < len(raw) and raw[i] not in ".[":
            i += 1
        name = raw[start:i]
        if not name:
            raise JsonPathError("Invalid field token in query.")
        tokens.append(_PathToken("field", name))

    return tokens


def _resolve_token(node: Any, token: _PathToken) -> list[Any]:
    if token.kind == "field":
        if isinstance(node, dict) and token.value in node:
            return [node[token.value]]
        return []

    if token.kind == "index":
        if not isinstance(node, list):
            return []
        index = int(token.value)
        if index < 0:
            index += len(node)
        if 0 <= index < len(node):
            return [node[index]]
        return []

    if token.kind == "wildcard":
        if isinstance(node, dict):
            return list(node.values())
        if isinstance(node, list):
            return list(node)
        return []

    return []


def extract_json_path(data: Any, query: str) -> list[Any]:
    """Extract all values matching a simple JSON query path.

    Query syntax:
    - Dot field access: ``message.text``
    - Array indexes: ``items[0]`` and ``items[-1]``
    - Wildcards: ``items[*].id`` or ``payload.*.id``
    - Quoted keys in brackets: ``['field.with.dots']``
    - Optional root prefix: ``$.message.text``
    """

    tokens = _parse_query(query)
    nodes = [data]
    for token in tokens:
        next_nodes: list[Any] = []
        for node in nodes:
            next_nodes.extend(_resolve_token(node, token))
        nodes = next_nodes
        if not nodes:
            break
    return nodes


def extract_json_paths(data: Any, queries: list[str], *, first: bool = False) -> dict[str, Any]:
    """Extract values for multiple JSON queries from one payload."""

    output: dict[str, Any] = {}
    for query in queries:
        matches = extract_json_path(data, query)
        output[query] = matches[0] if first and matches else (None if first else matches)
    return output


def load_json_file(path: str | Path) -> Any:
    """Load JSON from disk and return the parsed Python object."""

    file_path = Path(path).expanduser().resolve()
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
