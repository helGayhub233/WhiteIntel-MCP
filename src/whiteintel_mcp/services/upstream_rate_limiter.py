"""Small per-endpoint request pacer for the WhiteIntel API."""

from __future__ import annotations

import asyncio
import math
import os
import time
from collections.abc import Callable


DEFAULT_QPS = 0.3
QPS_ENV_VAR = "WHITEINTEL_UPSTREAM_QPS"


class RateLimitWaitExceeded(Exception):
    def __init__(self, retry_after: float):
        super().__init__("Request pacing exceeds the inline wait budget.")
        self.retry_after = retry_after


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

    def __init__(self, qps: float = DEFAULT_QPS, *, clock: Callable[[], float] = time.monotonic) -> None:
        if not math.isfinite(qps) or qps <= 0:
            raise ValueError("qps must be a positive finite number.")
        self.qps = qps
        self._cooldown = 1.0 / qps
        if not math.isfinite(self._cooldown):
            raise ValueError("qps must produce a finite pacing interval.")
        self._last_call: dict[tuple[str, str], float] = {}
        self._blocked_until: dict[tuple[str, str], float] = {}
        self._lock = asyncio.Lock()
        self._clock = clock

    @classmethod
    def from_environment(cls) -> "UpstreamRateLimiter":
        return cls(qps=qps_from_environment())

    async def wait(self, endpoint: str, apikey: str, *, max_wait_seconds: float | None = None) -> None:
        """Wait until the upstream cooldown has elapsed."""
        key = (endpoint, apikey)
        deadline = None if max_wait_seconds is None else self._clock() + max_wait_seconds
        while True:
            async with self._lock:
                now = self._clock()
                previous = self._last_call.get(key)
                available_at = now if previous is None else previous + self._cooldown
                available_at = max(available_at, self._blocked_until.get(key, now))
                wait_for = max(0.0, available_at - now)
                if not wait_for:
                    self._last_call[key] = now
                    return
                if deadline is not None and available_at > deadline:
                    raise RateLimitWaitExceeded(wait_for)
            # Recheck after sleeping: a 429 may extend the cooldown while queued.
            await asyncio.sleep(wait_for)

    async def defer(self, endpoint: str, apikey: str, seconds: float) -> None:
        """Apply the full provider cooldown to concurrent and later callers."""
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Provider cooldown must be nonnegative and finite.")
        key = (endpoint, apikey)
        async with self._lock:
            self._blocked_until[key] = max(self._blocked_until.get(key, 0), self._clock() + seconds)

    async def retry_after(self, endpoint: str, apikey: str) -> float:
        async with self._lock:
            return max(0.0, self._blocked_until.get((endpoint, apikey), 0) - self._clock())
