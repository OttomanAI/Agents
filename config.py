"""Centralised, validated configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    """Raised when a required environment variable is missing or invalid."""


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Required environment variable {name!r} is not set.")
    return value


def _optional(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application settings — all sourced from env vars at startup."""

    # Required
    openai_api_key: str = field(repr=False)
    telegram_bot_token: str = field(repr=False)
    pinecone_api_key: str = field(repr=False)
    pinecone_index_name: str = field(repr=True)
    pinecone_namespace: str = field(repr=True)

    # Tunables
    guardrail_model: str = "gpt-4.1-mini"
    chat_model: str = "gpt-4.1"
    poll_timeout_seconds: int = 120
    max_memory_entries: int = 20
    max_violations_per_day: int = 5

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent)

    @property
    def prompts_dir(self) -> Path:
        return self.base_dir / "prompts"

    @property
    def data_dir(self) -> Path:
        path = self.base_dir / "data"
        path.mkdir(exist_ok=True)
        return path

    @classmethod
    def from_env(cls) -> Settings:
        """Build a Settings instance from the current environment."""
        return cls(
            openai_api_key=_require("OPENAI_API_KEY"),
            telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
            pinecone_api_key=_require("PINECONE_API_KEY"),
            pinecone_index_name=_require("PINECONE_INDEX_NAME"),
            pinecone_namespace=_optional("PINECONE_NAMESPACE", ""),
            guardrail_model=_optional("GUARDRAIL_MODEL", "gpt-4.1-mini"),
            chat_model=_optional("CHAT_MODEL", "gpt-4.1"),
            poll_timeout_seconds=int(_optional("POLL_TIMEOUT_SECONDS", "120")),
            max_memory_entries=int(_optional("MAX_MEMORY_ENTRIES", "20")),
            max_violations_per_day=int(_optional("MAX_VIOLATIONS_PER_DAY", "5")),
        )
