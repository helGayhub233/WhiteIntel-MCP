from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

import httpx

from whiteintel_mcp.services.whiteintel_client import WhiteIntelClient


class RecordingRateLimiter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def wait(self, endpoint: str, apikey: str) -> None:
        self.calls.append((endpoint, apikey))


class WhiteIntelClientTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.limiter = RecordingRateLimiter()
        self.client = WhiteIntelClient(rate_limiter=self.limiter)  # type: ignore[arg-type]

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def _start_with_handler(self, handler) -> None:
        self.client._client = httpx.AsyncClient(  # noqa: SLF001 - isolated transport test
            transport=httpx.MockTransport(handler)
        )

    async def test_logical_tools_sharing_a_route_share_the_pacing_key(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"success": True})

        await self._start_with_handler(handler)
        body = {"apikey": "key"}
        await self.client.call("threat_feed", body)
        await self.client.call("threat_feed_darkweb_chatters", body)

        self.assertEqual(
            self.limiter.calls,
            [
                ("/get_threat_feeds.php", "key"),
                ("/get_threat_feeds.php", "key"),
            ],
        )

    async def test_429_without_retry_after_uses_documented_wait_message(self) -> None:
        responses = iter(
            (
                httpx.Response(
                    429,
                    json={"message": "Please wait 5 seconds between requests."},
                ),
                httpx.Response(200, json={"success": True, "results": []}),
            )
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return next(responses)

        await self._start_with_handler(handler)
        with patch(
            "whiteintel_mcp.services.whiteintel_client.asyncio.sleep",
            new=AsyncMock(),
        ) as sleep:
            result = await self.client.call("last_leaks", {"apikey": "key"})

        self.assertTrue(result["success"])
        sleep.assert_awaited_once_with(5.0)

    async def test_repeated_429_surfaces_normalized_retry_delay(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"message": "Slow down."})

        await self._start_with_handler(handler)
        with patch(
            "whiteintel_mcp.services.whiteintel_client.asyncio.sleep",
            new=AsyncMock(),
        ):
            result = await self.client.call("last_leaks", {"apikey": "key"})

        self.assertEqual(result["retry_after"], 5.0)

    async def test_non_object_json_is_returned_as_structured_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=["unexpected"])

        await self._start_with_handler(handler)
        result = await self.client.call("last_leaks", {"apikey": "key"})

        self.assertFalse(result["success"])
        self.assertEqual(result["http_status"], 200)
        self.assertIn("Invalid JSON object", result["error"])


if __name__ == "__main__":
    unittest.main()
