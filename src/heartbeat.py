"""Simple heartbeat trigger for runtime checks."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit periodic heartbeat messages")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between heartbeats")
    parser.add_argument("--count", type=int, default=1, help="Number of heartbeat messages to emit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.count < 1:
        raise ValueError("count must be >= 1")
    if args.interval < 0:
        raise ValueError("interval must be >= 0")

    for idx in range(args.count):
        now = datetime.now(timezone.utc).isoformat()
        print(f"heartbeat[{idx + 1}/{args.count}] {now}")
        if idx < args.count - 1:
            time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
