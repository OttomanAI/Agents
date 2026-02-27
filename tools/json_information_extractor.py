#!/usr/bin/env python3
"""Extract values from JSON payloads using dot/bracket paths.

Examples:
  python tools/json_information_extractor.py \
    --input-json '{"matches":[{"metadata":{"text":"hello"}}]}' \
    --path 'matches[0].metadata.text'

  python tools/json_information_extractor.py \
    --input-file output.json \
    --path 'message.id' \
    --path 'message.payload.headers[0].value'
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_json_input(input_json: str) -> Any:
    """Parse JSON input string into Python data."""
    cleaned = input_json.strip()
    if not cleaned:
        raise ValueError("input JSON must be a non-empty string")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON input: {exc}") from exc


def load_json_file(file_path: str) -> Any:
    """Load JSON payload from disk."""
    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"JSON file not found: {file_path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({file_path}): {exc}") from exc


def parse_json_path(path: str) -> list[str | int]:
    """Parse dot/bracket JSON path into access tokens.

    Supported examples:
      `a.b.c`
      `a[0].b`
      `matches[2].metadata.text`
    """
    raw = path.strip()
    if not raw:
        raise ValueError("path must be a non-empty string")

    tokens: list[str | int] = []
    part = ""
    index_mode = False
    index_buf = ""

    for char in raw:
        if index_mode:
            if char == "]":
                if not index_buf or not index_buf.isdigit():
                    raise ValueError(f"Invalid list index in path: {path}")
                tokens.append(int(index_buf))
                index_buf = ""
                index_mode = False
                continue
            index_buf += char
            continue

        if char == ".":
            if part:
                tokens.append(part)
                part = ""
            continue
        if char == "[":
            if part:
                tokens.append(part)
                part = ""
            index_mode = True
            index_buf = ""
            continue
        if char == "]":
            raise ValueError(f"Unexpected ']' in path: {path}")
        part += char

    if index_mode:
        raise ValueError(f"Unclosed list index in path: {path}")
    if part:
        tokens.append(part)
    if not tokens:
        raise ValueError("path must contain at least one token")
    return tokens


def extract_json_value(
    payload: Any,
    path: str,
    *,
    default: Any = None,
    strict: bool = False,
) -> Any:
    """Extract a value from JSON payload using path tokens."""
    tokens = parse_json_path(path)
    current: Any = payload

    for token in tokens:
        if isinstance(token, int):
            if not isinstance(current, list) or token < 0 or token >= len(current):
                if strict:
                    raise ValueError(f"Path not found: {path}")
                return default
            current = current[token]
            continue

        if not isinstance(current, dict) or token not in current:
            if strict:
                raise ValueError(f"Path not found: {path}")
            return default
        current = current[token]

    return current


def extract_json_values(
    payload: Any,
    paths: list[str],
    *,
    default: Any = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Extract multiple values from one payload."""
    if not paths:
        raise ValueError("at least one path is required")
    return {
        path: extract_json_value(payload, path, default=default, strict=strict)
        for path in paths
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract information from JSON payloads")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input-json", help="Raw JSON string input")
    source_group.add_argument("--input-file", help="Path to JSON file")
    parser.add_argument(
        "--path",
        action="append",
        required=True,
        help="JSON path using dot/bracket notation. Repeat for multiple values.",
    )
    parser.add_argument(
        "--default",
        default=None,
        help="Fallback value when a path is missing (ignored with --strict)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Raise error if any path is missing",
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="Output format for single-path extraction",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = (
        parse_json_input(args.input_json)
        if args.input_json is not None
        else load_json_file(args.input_file)
    )

    if len(args.path) == 1:
        value = extract_json_value(
            payload,
            args.path[0],
            default=args.default,
            strict=args.strict,
        )
        if args.output == "text":
            if isinstance(value, (dict, list)):
                print(json.dumps(value, ensure_ascii=True))
            else:
                print("" if value is None else str(value))
        else:
            print(json.dumps(value, indent=2, ensure_ascii=True))
        return 0

    values = extract_json_values(
        payload,
        args.path,
        default=args.default,
        strict=args.strict,
    )
    print(json.dumps(values, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
