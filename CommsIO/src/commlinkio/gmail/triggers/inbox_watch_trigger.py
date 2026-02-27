"""Gmail inbox watch trigger entrypoint."""

from __future__ import annotations

import logging

from commlinkio.gmail.clients import GmailWatchClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main() -> None:
    client = GmailWatchClient()
    client.start_watch()


if __name__ == "__main__":
    main()
