"""HTTP client for the WhiteIntel API."""

from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from whiteintel_mcp.services.upstream_rate_limiter import UpstreamRateLimiter


_ENDPOINT_PATHS: dict[str, str] = {
    "last_leaks": "/get_last_leaks.php",
    "threat_feed": "/get_threat_feeds.php",
    "threat_feed_darkweb_chatters": "/get_threat_feeds.php",
    "consumer_leaks": "/get_consumer_leaks.php",
    "corporate_leaks": "/get_corporate_leaks.php",
    "database_leaks": "/get_third_party_db_leaks.php",
    "overall_stats": "/get_overall_stats.php",
    "ip_leaks": "/get_leaks_by_ip.php",
    "computer_leaks": "/get_leaks_by_computer_name.php",
    "username_leaks": "/get_leaks_by_username.php",
    "lookalike_domains": "/get_lookalike_domains.php",
    "leaks_by_id": "/get_leaks_by_id.php",
    "watchlist_manage": "/watchlist_manage.php",
    "supplier": "/supplier_api.php",
    "audit_logs": "/get_audit_logs.php",
    "card_check": "/card_check.php",
}

_DEFAULT_BASE_URL = "https://api.whiteintel.io"
_DEFAULT_TIMEOUT = 30.0
MAX_RETRY_AFTER_SECONDS = 30.0
DEFAULT_429_RETRY_SECONDS = 5.0
_WAIT_SECONDS_PATTERN = re.compile(
    r"(?:wait|retry(?:\s+after)?)\D{0,20}(\d+(?:\.\d+)?)\s*seconds?",
    re.IGNORECASE,
)


def _retry_delay_seconds(result: dict[str, Any]) -> float:
    """Resolve Retry-After seconds, including HTTP dates and documented messages."""
    retry_after = result.get("retry_after")
    if retry_after is not None:
        try:
            return max(0.0, float(retry_after))
        except (TypeError, ValueError):
            if isinstance(retry_after, str):
                try:
                    retry_at = parsedate_to_datetime(retry_after)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=timezone.utc)
                    return max(
                        0.0,
                        (retry_at - datetime.now(timezone.utc)).total_seconds(),
                    )
                except (TypeError, ValueError, OverflowError):
                    pass

    for key in ("message", "error", "detail"):
        message = result.get(key)
        if isinstance(message, str) and (match := _WAIT_SECONDS_PATTERN.search(message)):
            return max(0.0, float(match.group(1)))
    return DEFAULT_429_RETRY_SECONDS


class WhiteIntelClient:
    """Thin async HTTP client with one upstream POST method."""

    def __init__(
        self,
        rate_limiter: UpstreamRateLimiter,
        base_url: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._rate_limiter = rate_limiter
        self._base_url = (
            base_url or os.getenv("WHITEINTEL_BASE_URL", _DEFAULT_BASE_URL)
        ).rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Create the underlying httpx connection pool."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers={"Content-Type": "application/json"},
            )

    async def aclose(self) -> None:
        """Close the connection pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def call(self, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
        """POST ``body`` to one WhiteIntel endpoint."""
        if self._client is None:
            raise RuntimeError("WhiteIntelClient not started; call start() first.")

        path = _ENDPOINT_PATHS.get(endpoint)
        if path is None:
            return {
                "success": False,
                "http_status": 400,
                "error": f"Unknown endpoint: {endpoint}",
            }

        # Pace by the actual upstream route. Logical MCP tools may share one route.
        await self._rate_limiter.wait(path, str(body.get("apikey", "")))
        result = await self._post(path, body)

        if result.get("http_status") == 429:
            retry_after = _retry_delay_seconds(result)
            await asyncio.sleep(min(retry_after, MAX_RETRY_AFTER_SECONDS))
            result = await self._post(path, body)
            if result.get("http_status") == 429:
                result.setdefault("retry_after", _retry_delay_seconds(result))

        return result

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        assert self._client is not None
        url = f"{self._base_url}{path}"

        try:
            response = await self._client.post(url, json=body)
        except httpx.TimeoutException:
            return {
                "success": False,
                "http_status": 504,
                "error": "Upstream request timed out.",
            }
        except httpx.RequestError as exc:
            return {
                "success": False,
                "http_status": 502,
                "error": f"Upstream request failed: {exc}",
            }

        retry_after = response.headers.get("Retry-After")
        try:
            decoded = response.json()
        except ValueError:
            data = {
                "success": False,
                "error": f"Invalid JSON response from upstream (HTTP {response.status_code}).",
            }
        else:
            if isinstance(decoded, dict):
                data = decoded
            else:
                data = {
                    "success": False,
                    "error": (
                        "Invalid JSON object from upstream "
                        f"(HTTP {response.status_code})."
                    ),
                }

        data["http_status"] = response.status_code
        if retry_after is not None:
            data["retry_after"] = retry_after
        data.setdefault("success", 200 <= response.status_code < 300)
        return data
