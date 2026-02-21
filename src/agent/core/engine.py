"""Core response generation for the starter agent."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AgentRequest:
    """Input payload consumed by the agent engine."""

    content: str
    system_message: str
    knowledge_base: str


@dataclass(frozen=True)
class AgentResponse:
    """Structured response emitted by the agent engine."""

    content: str
    created_at: datetime


class AgentEngine:
    """Deterministic formatter for agent input payloads."""

    def respond(self, request: AgentRequest) -> AgentResponse:
        content = self._require_text(request.content, "content")
        system_message = self._require_text(request.system_message, "system_message")
        knowledge_base = self._require_text(request.knowledge_base, "knowledge_base")

        rendered = self._render_text(
            content=content,
            system_message=system_message,
            knowledge_base=knowledge_base,
        )
        return AgentResponse(content=rendered, created_at=datetime.now(timezone.utc))

    @staticmethod
    def _require_text(value: str, field: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{field} must be a non-empty string")
        return cleaned

    @staticmethod
    def _render_text(content: str, system_message: str, knowledge_base: str) -> str:
        kb_lines = [line.strip() for line in knowledge_base.splitlines() if line.strip()]
        kb_text = " ".join(kb_lines)
        return (
            f"System message: {system_message}\n"
            f"Knowledge base: {kb_text}\n"
            f"Output text: {content}"
        )
