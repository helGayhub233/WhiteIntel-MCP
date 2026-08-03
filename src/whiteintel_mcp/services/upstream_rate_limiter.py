"""Small per-endpoint request pacer for the WhiteIntel API."""

from __future__ import annotations

import asyncio
import math
import os
import time


DEFAULT_QPS = 0.2
QPS_ENV_VAR = "WHITEINTEL_UPSTREAM_QPS"


def qps_from_environment() -> float:
    """Read the conservative local pacing rate from the environment."""
    raw = os.getenv(QPS_ENV_VAR)
    if raw is None or not raw.strip():
        return DEFAULT_QPS
    try:
        qps = float(raw)
    except ValueError as exc:
        raise ValueError(f"{QPS_ENV_VAR} must be a positive number.") from exc
    if not math.isfinite(qps) or qps <= 0:
        raise ValueError(f"{QPS_ENV_VAR} must be a positive finite number.")
    return qps


class UpstreamRateLimiter:
    """In-memory cooldown keyed by ``(endpoint, apikey)``."""

    def __init__(self, qps: float = DEFAULT_QPS) -> None:
        if not math.isfinite(qps) or qps <= 0:
            raise ValueError("qps must be a positive finite number.")
        self.qps = qps
        self._cooldown = 1.0 / qps
        self._last_call: dict[tuple[str, str], float] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def from_environment(cls) -> "UpstreamRateLimiter":
        return cls(qps=qps_from_environment())

    async def wait(self, endpoint: str, apikey: str) -> None:
        """Wait until the upstream cooldown has elapsed."""
        key = (endpoint, apikey)
        async with self._lock:
            now = time.monotonic()
            available_at = self._last_call.get(key, 0.0) + self._cooldown
            wait_for = max(0.0, available_at - now)
            self._last_call[key] = now + wait_for

        if wait_for:
            await asyncio.sleep(wait_for)
