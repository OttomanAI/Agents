"""Configuration loader with env-over-yaml precedence."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

_DEFAULTS: dict[str, str] = {
    "openai_api_key": "",
    "openai_model": "gpt-4o",
    "embedding_model": "text-embedding-3-small",
    "knowledge_base_path": "knowledge_base/documents",
    "system_message": (
        "You are a helpful AI assistant with access to a knowledge base. "
        "When answering questions, use the provided context from the knowledge base "
        "to give accurate, grounded responses. If the context does not contain "
        "relevant information, say so clearly rather than guessing."
    ),
}

_ENV_MAP: dict[str, str] = {
    "openai_api_key": "OPENAI_API_KEY",
    "openai_model": "OPENAI_MODEL",
    "embedding_model": "EMBEDDING_MODEL",
    "knowledge_base_path": "KNOWLEDGE_BASE_PATH",
    "system_message": "SYSTEM_MESSAGE",
}


class Config:
    """Unified config object sourced from defaults, yaml, and environment."""

    def __init__(self, config_path: str | None = None, env_only: bool = False) -> None:
        load_dotenv()

        self._explicit_config_path = config_path is not None
        self._config_path = Path(config_path).expanduser() if config_path else Path("config.yaml")
        self._data: dict[str, str] = dict(_DEFAULTS)

        if not env_only:
            self._load_yaml_values()
        self._load_environment_values()

    def _load_yaml_values(self) -> None:
        if not self._config_path.exists():
            if self._explicit_config_path:
                raise FileNotFoundError(f"Config file not found: {self._config_path}")
            return
        if not self._config_path.is_file():
            raise ValueError(f"Config path is not a file: {self._config_path}")

        with self._config_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        if not isinstance(payload, dict):
            raise ValueError(f"Config file must contain a YAML mapping: {self._config_path}")

        for key in _DEFAULTS:
            value = payload.get(key)
            if value is None:
                continue
            normalized = str(value).strip()
            if normalized:
                self._data[key] = normalized

    def _load_environment_values(self) -> None:
        for key, env_var in _ENV_MAP.items():
            value = os.environ.get(env_var)
            if value and value.strip():
                self._data[key] = value.strip()

    @property
    def openai_api_key(self) -> str:
        return self._data["openai_api_key"]

    @property
    def openai_model(self) -> str:
        return self._data["openai_model"]

    @property
    def embedding_model(self) -> str:
        return self._data["embedding_model"]

    @property
    def knowledge_base_path(self) -> str:
        return self._data["knowledge_base_path"]

    @property
    def system_message(self) -> str:
        return self._data["system_message"]

    @property
    def config_path(self) -> str:
        return str(self._config_path)

    def validate(self) -> None:
        if not self.openai_api_key:
            raise ValueError(
                "OpenAI API key is not set. Set OPENAI_API_KEY or add openai_api_key to config.yaml."
            )

    def to_safe_dict(self) -> dict[str, Any]:
        masked_key = "<not set>"
        if self.openai_api_key:
            visible_prefix = self.openai_api_key[:8]
            masked_key = f"{visible_prefix}..."

        return {
            "openai_api_key": masked_key,
            "openai_model": self.openai_model,
            "embedding_model": self.embedding_model,
            "knowledge_base_path": self.knowledge_base_path,
            "system_message": self.system_message,
            "config_path": self.config_path,
        }

    def __repr__(self) -> str:
        safe = self.to_safe_dict()
        return (
            "Config("
            f"openai_model={safe['openai_model']!r}, "
            f"embedding_model={safe['embedding_model']!r}, "
            f"knowledge_base_path={safe['knowledge_base_path']!r}, "
            f"openai_api_key={safe['openai_api_key']!r}"
            ")"
        )
