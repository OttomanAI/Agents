"""RAG-powered AI agent that answers questions using a knowledge base."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from Agents.config import Config
from Agents.knowledge_base import KnowledgeBase

if TYPE_CHECKING:  # pragma: no cover
    from openai import OpenAI


class RAGAgent:
    """Conversational agent backed by retrieval-augmented generation."""

    def __init__(
        self,
        config: Config,
        knowledge_base: KnowledgeBase,
        openai_client: OpenAI | None = None,
    ) -> None:
        if openai_client is None:
            try:
                from openai import OpenAI as OpenAIClient
            except ImportError as exc:  # pragma: no cover - runtime dependency
                raise RuntimeError("openai is required. Install with: pip install openai") from exc
            openai_client = OpenAIClient(api_key=config.openai_api_key)

        self._config = config
        self._kb = knowledge_base
        self._client = openai_client
        self._history: list[dict[str, str]] = []

    def ask(self, question: str, n_context: int = 3) -> str:
        if not question.strip():
            raise ValueError("question must not be empty")
        if n_context <= 0:
            raise ValueError("n_context must be > 0")

        context_chunks = self._kb.query(question, n_results=n_context)
        context_block = self._format_context(context_chunks)
        messages = self._build_messages(question, context_block)

        response = self._client.chat.completions.create(
            model=self._config.openai_model,
            messages=messages,
        )

        assistant_reply = (response.choices[0].message.content or "").strip()
        if not assistant_reply:
            assistant_reply = "I could not generate a response."

        self._history.append({"role": "user", "content": question})
        self._history.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply

    def reset_history(self) -> None:
        self._history.clear()

    @property
    def history(self) -> list[dict[str, str]]:
        return list(self._history)

    @staticmethod
    def _format_context(chunks: list[dict[str, Any]]) -> str:
        if not chunks:
            return "No relevant context found in the knowledge base."

        parts: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.get("source", "unknown")
            text = str(chunk.get("text", ""))
            parts.append(f"[Source {i}: {source}]\n{text}")
        return "\n\n".join(parts)

    def _build_messages(self, question: str, context: str) -> list[dict[str, str]]:
        system = (
            f"{self._config.system_message}\n\n"
            "--- Retrieved Context ---\n"
            f"{context}\n"
            "--- End Context ---\n\n"
            "Use the context above to help answer the user's question. "
            "Cite the source when possible."
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        messages.extend(self._history[-10:])
        messages.append({"role": "user", "content": question})
        return messages
