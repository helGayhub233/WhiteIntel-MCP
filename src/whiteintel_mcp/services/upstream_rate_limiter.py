"""Small per-endpoint request pacer for the WhiteIntel API."""

from __future__ import annotations

import asyncio
import time


DEFAULT_QPS = 0.2
DEFAULT_COOLDOWN_SECONDS = 1.0 / DEFAULT_QPS


class UpstreamRateLimiter:
    """In-memory cooldown keyed by ``(endpoint, apikey)``."""

    def __init__(self) -> None:
        self._last_call: dict[tuple[str, str], float] = {}
        self._lock = asyncio.Lock()

    async def wait(self, endpoint: str, apikey: str) -> None:
        """Wait until the upstream cooldown has elapsed."""
        key = (endpoint, apikey)
        cooldown = DEFAULT_COOLDOWN_SECONDS

        async with self._lock:
            now = time.monotonic()
            available_at = self._last_call.get(key, 0.0) + cooldown
            wait_for = max(0.0, available_at - now)
            self._last_call[key] = now + wait_for

        if wait_for:
            await asyncio.sleep(wait_for)
