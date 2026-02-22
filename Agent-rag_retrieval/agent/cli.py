"""Command-line interface for the RAG retrieval agent."""

from __future__ import annotations

import argparse
import logging
import sys

from openai import OpenAI

from agent.config import Config
from agent.knowledge_base import KnowledgeBase
from agent.rag_agent import RAGAgent

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG retrieval agent CLI")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a YAML config file (default: ./config.yaml if present).",
    )
    parser.add_argument(
        "--env-only",
        action="store_true",
        help="Ignore config.yaml and use only environment variables/defaults.",
    )
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="Run one question and exit (non-interactive mode).",
    )
    parser.add_argument(
        "--context-chunks",
        type=int,
        default=3,
        help="How many retrieved chunks to pass to the model per question.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Application log level.",
    )
    return parser


def _build_agent(config: Config) -> tuple[KnowledgeBase, RAGAgent]:
    client = OpenAI(api_key=config.openai_api_key)
    kb = KnowledgeBase(openai_client=client, embedding_model=config.embedding_model)
    loaded_chunks = kb.load_directory(config.knowledge_base_path)
    logger.info("Knowledge base loaded: %s chunks from %s", loaded_chunks, config.knowledge_base_path)
    agent = RAGAgent(config=config, knowledge_base=kb, openai_client=client)
    return kb, agent


def _interactive_loop(agent: RAGAgent, context_chunks: int) -> int:
    print("\nRAG Agent ready. Type your questions below (type 'quit' to exit).\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            return 0

        try:
            answer = agent.ask(question, n_context=context_chunks)
            print(f"\nAgent: {answer}\n")
        except Exception as exc:
            print(f"\n[Error] {exc}\n", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")

    try:
        config = Config(config_path=args.config, env_only=args.env_only)
        config.validate()
    except Exception as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    logger.info("Config loaded: %s", config)

    try:
        _, agent = _build_agent(config)
    except Exception as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        return 2

    if args.question:
        try:
            answer = agent.ask(args.question, n_context=args.context_chunks)
            print(answer)
            return 0
        except Exception as exc:
            print(f"Query error: {exc}", file=sys.stderr)
            return 2

    return _interactive_loop(agent, args.context_chunks)


if __name__ == "__main__":
    raise SystemExit(main())
