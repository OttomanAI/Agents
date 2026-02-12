"""Configuration loader that supports both environment variables and a YAML config file.

Priority order:
  1. Environment variables (highest)
  2. config.yaml file
  3. Built-in defaults (lowest)
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

_DEFAULTS = {
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

# Maps config-file keys to their corresponding environment variable names.
_ENV_MAP = {
    "openai_api_key": "OPENAI_API_KEY",
    "openai_model": "OPENAI_MODEL",
    "embedding_model": "EMBEDDING_MODEL",
    "knowledge_base_path": "KNOWLEDGE_BASE_PATH",
    "system_message": "SYSTEM_MESSAGE",
}


class Config:
    """Unified configuration object.

    Usage::

        cfg = Config()                       # auto-detect .env / config.yaml
        cfg = Config(config_path="my.yaml")  # explicit YAML path
        cfg = Config(env_only=True)          # ignore YAML, env-vars only
    """

    def __init__(
        self,
        config_path: str | None = None,
        env_only: bool = False,
    ) -> None:
        # Load .env file if present (does NOT override existing env vars)
        load_dotenv()

        # Start from defaults
        self._data: dict[str, str] = dict(_DEFAULTS)

        # Layer in YAML config if available
        if not env_only:
            yaml_path = Path(config_path) if config_path else Path("config.yaml")
            if yaml_path.is_file():
                with open(yaml_path) as f:
                    yaml_data = yaml.safe_load(f) or {}
                for key in _DEFAULTS:
                    if key in yaml_data and yaml_data[key]:
                        self._data[key] = str(yaml_data[key]).strip()

        # Layer in environment variables (highest priority)
        for key, env_var in _ENV_MAP.items():
            value = os.environ.get(env_var)
            if value:
                self._data[key] = value.strip()

    # --- public accessors ---------------------------------------------------

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

    def validate(self) -> None:
        """Raise ``ValueError`` if required settings are missing."""
        if not self.openai_api_key:
            raise ValueError(
                "OpenAI API key is not set. "
                "Set the OPENAI_API_KEY environment variable or add "
                "'openai_api_key' to config.yaml."
            )

    def __repr__(self) -> str:
        masked_key = self.openai_api_key[:8] + "..." if self.openai_api_key else "<not set>"
        return (
            f"Config(model={self.openai_model!r}, "
            f"embedding={self.embedding_model!r}, "
            f"key={masked_key})"
        )
