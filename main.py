"""CLI entry point for the RAG agent.

Run interactively::

    python main.py

Or with a specific config file::

    python main.py --config my_config.yaml
"""

import argparse
import sys

from agent.config import Config
from agent.knowledge_base import KnowledgeBase
from agent.rag_agent import RAGAgent
from openai import OpenAI


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG AI Agent CLI")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a YAML config file (default: config.yaml if it exists)",
    )
    parser.add_argument(
        "--env-only",
        action="store_true",
        help="Ignore config.yaml and only use environment variables",
    )
    args = parser.parse_args()

    # --- Configuration ---
    cfg = Config(config_path=args.config, env_only=args.env_only)
    cfg.validate()
    print(f"Config loaded: {cfg}")

    # --- OpenAI client ---
    client = OpenAI(api_key=cfg.openai_api_key)

    # --- Knowledge Base ---
    kb = KnowledgeBase(openai_client=client, embedding_model=cfg.embedding_model)
    n_chunks = kb.load_directory(cfg.knowledge_base_path)
    print(f"Knowledge base loaded: {n_chunks} chunks from '{cfg.knowledge_base_path}'")

    # --- Agent ---
    agent = RAGAgent(config=cfg, knowledge_base=kb)

    # --- Interactive loop ---
    print("\nRAG Agent ready. Type your questions below (type 'quit' to exit).\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        try:
            answer = agent.ask(question)
            print(f"\nAgent: {answer}\n")
        except Exception as exc:
            print(f"\n[Error] {exc}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
