from __future__ import annotations

import unittest
from types import SimpleNamespace

from agent.rag_agent import RAGAgent


class _FakeKnowledgeBase:
    def __init__(self) -> None:
        self.last_question: str | None = None
        self.last_n_results: int | None = None

    def query(self, question: str, n_results: int = 3) -> list[dict]:
        self.last_question = question
        self.last_n_results = n_results
        return [
            {"text": "Alpha details", "source": "doc_a.md", "distance": 0.1},
            {"text": "Beta details", "source": "doc_b.md", "distance": 0.2},
        ]


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.captured_model: str | None = None
        self.captured_messages: list[dict[str, str]] | None = None

        def create(*, model: str, messages: list[dict[str, str]]):
            self.captured_model = model
            self.captured_messages = messages
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Synthetic answer"))]
            )

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


class RAGAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimpleNamespace(
            openai_api_key="ignored-for-test",
            openai_model="gpt-test-model",
            system_message="System prompt",
        )
        self.kb = _FakeKnowledgeBase()
        self.client = _FakeOpenAIClient()
        self.agent = RAGAgent(config=self.config, knowledge_base=self.kb, openai_client=self.client)

    def test_ask_uses_context_and_updates_history(self) -> None:
        answer = self.agent.ask("What is alpha?", n_context=2)
        self.assertEqual(answer, "Synthetic answer")
        self.assertEqual(self.kb.last_question, "What is alpha?")
        self.assertEqual(self.kb.last_n_results, 2)
        self.assertEqual(len(self.agent.history), 2)
        assert self.client.captured_messages is not None
        self.assertIn("Retrieved Context", self.client.captured_messages[0]["content"])

    def test_ask_rejects_empty_question(self) -> None:
        with self.assertRaises(ValueError):
            self.agent.ask("   ")

    def test_reset_history(self) -> None:
        self.agent.ask("Q1")
        self.assertTrue(self.agent.history)
        self.agent.reset_history()
        self.assertEqual(self.agent.history, [])


if __name__ == "__main__":
    unittest.main()
