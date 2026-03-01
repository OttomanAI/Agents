"""Simple JSON-file conversation memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class Memory:
    """Persist conversation history to a JSON file.

    Parameters
    ----------
    path:
        File path for the JSON store.  Created automatically on first save.
    """

    def __init__(self, path: str | Path = "memory.json", max_entries: int = 10) -> None:
        self._path = Path(path)
        self._max = max_entries
        self._entries: list[dict] = []
        if self._path.exists():
            self._entries = self.load()

    # -- public API ----------------------------------------------------------

    @property
    def history(self) -> list[dict]:
        """Return the full conversation history."""
        return list(self._entries)

    def load(self) -> list[dict]:
        """Read the JSON file and return its contents."""
        text = self._path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        return json.loads(text)

    def save(self, role: str, content: str) -> dict:
        """Append an entry and write immediately.

        Returns the saved entry.
        """
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]
        self._write()
        return entry

    def clear(self) -> None:
        """Empty the memory file."""
        self._entries = []
        self._write()

    # -- internals -----------------------------------------------------------

    def _write(self) -> None:
        self._path.write_text(
            json.dumps(self._entries, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
