"""HTTP client for the WhiteIntel API.

Manages an httpx AsyncClient connection pool with lifecycle hooks
and endpoint path resolution.  Every upstream call flows through
UpstreamRateLimiter before the actual POST.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from whiteintel_mcp.services.upstream_rate_limiter import UpstreamRateLimiter


# Maps internal endpoint names to WhiteIntel API paths.
_ENDPOINT_PATH_MAP: dict[str, str] = {
    "last_leaks": "/get_last_leaks.php",
    "threat_feed": "/get_threat_feeds.php",
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
}

_DEFAULT_BASE_URL = "https://api.whiteintel.io"
_DEFAULT_TIMEOUT = 30.0


class WhiteIntelClient:
    """Async HTTP client for WhiteIntel API with built-in rate limiting."""

    def __init__(
        self,
        rate_limiter: UpstreamRateLimiter,
        base_url: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._rate_limiter = rate_limiter
        self._base_url = (base_url or os.getenv("WHITEINTEL_BASE_URL", _DEFAULT_BASE_URL)).rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Create the underlying httpx connection pool."""
        if self._client is not None:
            return
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            headers={"Content-Type": "application/json"},
        )

    async def aclose(self) -> None:
        """Close the connection pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Core call
    # ------------------------------------------------------------------

    async def call(self, endpoint_name: str, body: dict[str, Any]) -> dict[str, Any]:
        """POST *body* to *endpoint_name* after waiting for rate-limit clearance.

        Returns a dict with at least ``success``, ``http_status``, and
        the upstream JSON payload (or error details).
        """
        if self._client is None:
            raise RuntimeError("WhiteIntelClient not started — call start() first.")

        path = _ENDPOINT_PATH_MAP.get(endpoint_name)
        if path is None:
            return {
                "success": False,
                "http_status": 400,
                "error": f"Unknown endpoint: {endpoint_name}",
            }

        apikey = body.get("apikey", "")
        await self._rate_limiter.wait(endpoint_name, apikey)

        url = f"{self._base_url}{path}"

        # Remove apikey from the loggable payload sent upstream
        # (it is still included — the upstream needs it).
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

        http_status = response.status_code

        # Forward Retry-After header if present.
        retry_after = response.headers.get("Retry-After")

        try:
            data: dict[str, Any] = response.json()
        except ValueError:
            if http_status in {401, 403}:
                error = f"WhiteIntel authentication or permission failure (HTTP {http_status}); response was not JSON."
            else:
                error = f"Invalid JSON response from upstream (HTTP {http_status})."
            data = {
                "success": False,
                "error": error,
            }

        # Ensure http_status is always present.
        data["http_status"] = http_status

        # Forward Retry-After when available.
        if retry_after is not None:
            data["retry_after"] = retry_after

        # Inject success when not already present (mirrors upstream behavior).
        if "success" not in data:
            data["success"] = 200 <= http_status < 300

        return data
