"""Backwards-compatible CLI entry point.

Prefer running ``python -m agent.cli`` for direct module execution.
"""

from agent.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
