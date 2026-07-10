"""Per-endpoint + per-API-key request rate limiter for WhiteIntel API.

Based on WhiteIntel_API_Rate_Limiting_Report.md:
- Most endpoints require a 5-second cool-down between requests.
- Database Leaks API requires only 1 second.
- Rate limiting is tracked per (endpoint_name, apikey) tuple.
"""

from __future__ import annotations

import asyncio
import time
from typing import ClassVar


# Cool-down period (seconds) per endpoint name.
_COOLDOWN_MAP: dict[str, float] = {
    "database_leaks": 1.0,
}
_DEFAULT_COOLDOWN: float = 5.0


class UpstreamRateLimiter:
    """In-memory async rate limiter keyed by (endpoint, apikey)."""

    def __init__(self) -> None:
        self._last_call: dict[tuple[str, str], float] = {}
        self._lock = asyncio.Lock()

    def _cooldown(self, endpoint_name: str) -> float:
        return _COOLDOWN_MAP.get(endpoint_name, _DEFAULT_COOLDOWN)

    async def wait(self, endpoint_name: str, apikey: str) -> None:
        """Block until the cool-down period for (endpoint, apikey) has elapsed."""
        key = (endpoint_name, apikey)
        cooldown = self._cooldown(endpoint_name)

        async with self._lock:
            last = self._last_call.get(key, 0.0)
            now = time.monotonic()
            elapsed = now - last
            if elapsed < cooldown:
                wait_for = cooldown - elapsed
            else:
                wait_for = 0.0
            self._last_call[key] = now + wait_for

        if wait_for > 0:
            await asyncio.sleep(wait_for)
