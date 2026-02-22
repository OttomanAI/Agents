"""Gmail watch client scaffold.

Replace placeholders with Google API integration when credentials and topics are defined.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class GmailWatchClient:
    """Starts/stops Gmail watch subscriptions."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def start_watch(self) -> None:
        """Start Gmail push watch.

        This is intentionally a scaffold until Google credentials/topic wiring is added.
        """
        logger.info("Gmail watch scaffold invoked. Configure Google API credentials to enable.")
