"""CLI tool to extract specific values from a JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from commlinkio.core import JsonPathError, extract_json_paths, load_json_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="commlinkio-json-extract",
        description="Extract specific values from a JSON file using query paths.",
    )
    parser.add_argument("json_file", type=Path, help="Path to the JSON file.")
    parser.add_argument(
        "-q",
        "--query",
        action="append",
        required=True,
        help=(
            "Extraction query path. Repeat for multiple queries. "
            "Examples: message.text, payload.items[*].id, $.updates[-1].chat.id"
        ),
    )
    parser.add_argument(
        "--first",
        action="store_true",
        help="Return only the first match for each query (or null if none).",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help="Exit with code 2 if any query has no matches.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty-formatted JSON.",
    )
    return parser


def _format_output(payload: dict[str, Any], compact: bool) -> str:
    if compact:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        data = load_json_file(args.json_file)
        results = extract_json_paths(data, args.query, first=args.first)
    except FileNotFoundError:
        print(f"File not found: {args.json_file}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {args.json_file}: {exc}", file=sys.stderr)
        return 2
    except JsonPathError as exc:
        print(f"Invalid query path: {exc}", file=sys.stderr)
        return 2

    if args.required:
        missing_queries = [
            query
            for query in args.query
            if (results[query] is None if args.first else len(results[query]) == 0)
        ]
        if missing_queries:
            print(
                "Missing required query matches: " + ", ".join(missing_queries),
                file=sys.stderr,
            )
            return 2

    output = {
        "file": str(args.json_file),
        "results": results,
    }
    print(_format_output(output, args.compact))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
