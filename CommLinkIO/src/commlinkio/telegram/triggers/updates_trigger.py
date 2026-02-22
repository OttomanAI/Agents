"""Telegram updates trigger entrypoint."""

from __future__ import annotations

import json
import logging
from typing import Any

from commlinkio.telegram.readers import TelegramUpdateReader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class TelegramUpdatesTrigger:
    """Binds a Telegram update reader to an output sink."""

    def __init__(self) -> None:
        self.reader = TelegramUpdateReader(on_update=self.handle)

    @staticmethod
    def handle(data: dict[str, Any]) -> None:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

    def run(self) -> None:
        self.reader.start()


def main() -> None:
    TelegramUpdatesTrigger().run()


if __name__ == "__main__":
    main()
