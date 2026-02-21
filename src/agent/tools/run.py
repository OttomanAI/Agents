"""CLI entry point for generating an agent response."""

from __future__ import annotations

import argparse

from agent.core import AgentEngine, AgentRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the starter agent")
    parser.add_argument("--content", required=True, help="Content to process")
    parser.add_argument("--system-message", required=True, help="System instruction text")
    parser.add_argument("--knowledge-base", required=True, help="Knowledge base context")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = AgentEngine()
    request = AgentRequest(
        content=args.content,
        system_message=args.system_message,
        knowledge_base=args.knowledge_base,
    )
    response = engine.respond(request)
    print(response.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
