"""RAG-powered AI agent that answers questions using a knowledge base.

The agent:
1. Receives a user query.
2. Retrieves relevant context from the ``KnowledgeBase``.
3. Sends the context + query to OpenAI with the configured system message.
4. Returns the model's response.
"""

from openai import OpenAI

from agent.config import Config
from agent.knowledge_base import KnowledgeBase


class RAGAgent:
    """Conversational agent backed by retrieval-augmented generation.

    Parameters
    ----------
    config:
        Application configuration (API key, model names, system message, etc.).
    knowledge_base:
        An initialised ``KnowledgeBase`` instance for document retrieval.
    """

    def __init__(self, config: Config, knowledge_base: KnowledgeBase) -> None:
        self._config = config
        self._kb = knowledge_base
        self._client = OpenAI(api_key=config.openai_api_key)
        self._history: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ask(self, question: str, n_context: int = 3) -> str:
        """Ask the agent a question and get a response.

        Parameters
        ----------
        question:
            The user's question.
        n_context:
            Number of knowledge-base chunks to retrieve for context.

        Returns
        -------
        str
            The assistant's response text.
        """
        # Retrieve relevant context
        context_chunks = self._kb.query(question, n_results=n_context)
        context_block = self._format_context(context_chunks)

        # Build the message list
        messages = self._build_messages(question, context_block)

        # Call OpenAI
        response = self._client.chat.completions.create(
            model=self._config.openai_model,
            messages=messages,
        )

        assistant_reply = response.choices[0].message.content

        # Keep conversation history
        self._history.append({"role": "user", "content": question})
        self._history.append({"role": "assistant", "content": assistant_reply})

        return assistant_reply

    def reset_history(self) -> None:
        """Clear conversation history to start fresh."""
        self._history.clear()

    @property
    def history(self) -> list[dict]:
        """Return a copy of the conversation history."""
        return list(self._history)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _format_context(chunks: list[dict]) -> str:
        """Format retrieved chunks into a single context string."""
        if not chunks:
            return "No relevant context found in the knowledge base."

        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk["text"]
            parts.append(f"[Source {i}: {source}]\n{text}")
        return "\n\n".join(parts)

    def _build_messages(self, question: str, context: str) -> list[dict]:
        """Assemble the full message list for the OpenAI API call."""
        system = (
            f"{self._config.system_message}\n\n"
            "--- Retrieved Context ---\n"
            f"{context}\n"
            "--- End Context ---\n\n"
            "Use the context above to help answer the user's question. "
            "Cite the source when possible."
        )

        messages: list[dict] = [{"role": "system", "content": system}]

        # Include recent conversation history for multi-turn support
        messages.extend(self._history[-10:])

        messages.append({"role": "user", "content": question})
        return messages
