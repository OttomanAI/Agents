from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.config import Config


class ConfigTests(unittest.TestCase):
    def test_env_overrides_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.yaml"
            config_path.write_text(
                "openai_api_key: yaml-key\nopenai_model: gpt-from-yaml\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key", "OPENAI_MODEL": "gpt-from-env"}, clear=True):
                with patch("agent.config.load_dotenv", return_value=False):
                    config = Config(config_path=str(config_path))

            self.assertEqual(config.openai_api_key, "env-key")
            self.assertEqual(config.openai_model, "gpt-from-env")

    def test_env_only_ignores_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.yaml"
            config_path.write_text("openai_api_key: yaml-key\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                with patch("agent.config.load_dotenv", return_value=False):
                    config = Config(config_path=str(config_path), env_only=True)

            self.assertEqual(config.openai_api_key, "")

    def test_explicit_missing_path_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(FileNotFoundError):
                with patch("agent.config.load_dotenv", return_value=False):
                    Config(config_path="/tmp/does-not-exist/config.yaml")

    def test_safe_dict_masks_key(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-1234567890"}, clear=True):
            with patch("agent.config.load_dotenv", return_value=False):
                config = Config(env_only=True)
                safe = config.to_safe_dict()

        self.assertEqual(safe["openai_api_key"], "sk-test-...")


if __name__ == "__main__":
    unittest.main()
