from __future__ import annotations

import unittest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx

from whiteintel_mcp.services.whiteintel_client import WhiteIntelClient, _retry_delay_seconds
from whiteintel_mcp.services.upstream_rate_limiter import RateLimitWaitExceeded, UpstreamRateLimiter


class RecordingRateLimiter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.cooldowns: list[tuple[str, str, float]] = []

    async def wait(self, endpoint: str, apikey: str, *, max_wait_seconds=None) -> None:
        self.calls.append((endpoint, apikey))

    async def defer(self, endpoint: str, apikey: str, seconds: float) -> None:
        self.cooldowns.append((endpoint, apikey, seconds))

    async def retry_after(self, endpoint: str, apikey: str) -> float:
        return 0.0


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
        self.assertEqual(len(self.limiter.calls), 2)
        self.assertEqual(self.limiter.cooldowns, [("/get_last_leaks.php", "key", 5.0)])

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

    async def test_http_and_body_success_must_agree(self):
        for status, body in (
            (200, {}), (200, {"error": "Invalid request."}),
            (200, {"success": "false"}), (200, {"success": 1}),
            (200, {"success": True, "error": "Invalid request."}),
            (500, {"success": True}), (403, {"success": True}),
        ):
            with self.subTest(status=status, body=body):
                await self.client.aclose()
                await self._start_with_handler(lambda request: httpx.Response(status, json=body))
                result = await self.client.call("last_leaks", {"apikey": "key"})
                self.assertIs(result["success"], False)
                self.assertEqual(result["http_status"], status)

    async def test_timeout_and_invalid_json_are_failures(self):
        def timeout(request):
            raise httpx.ReadTimeout("fixture timeout", request=request)
        await self._start_with_handler(timeout)
        self.assertEqual((await self.client.call("last_leaks", {"apikey": "key"}))["http_status"], 504)
        await self.client.aclose()
        await self._start_with_handler(lambda request: httpx.Response(200, text="not JSON"))
        self.assertFalse((await self.client.call("last_leaks", {"apikey": "key"}))["success"])



class WhiteIntelStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_unstarted_client_reports_explicit_runtime_error(self) -> None:
        client = WhiteIntelClient(rate_limiter=RecordingRateLimiter())  # type: ignore[arg-type]
        with self.assertRaisesRegex(RuntimeError, "not started"):
            await client._post("/fixture", {"apikey": "key"})  # noqa: SLF001


class ProviderCooldownTests(unittest.IsolatedAsyncioTestCase):
    async def test_long_cooldown_prevents_retry_and_later_same_key_requests(self):
        clock = [100.0]
        limiter = UpstreamRateLimiter(qps=1, clock=lambda: clock[0])
        client = WhiteIntelClient(rate_limiter=limiter)
        requests = []
        def handler(request):
            requests.append(request)
            return httpx.Response(429, headers={"Retry-After": "120"}, json={"error": "Slow down."})
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            with patch("whiteintel_mcp.services.whiteintel_client.asyncio.sleep", new=AsyncMock()) as sleep:
                first = await client.call("last_leaks", {"apikey": "key"})
                second = await client.call("last_leaks", {"apikey": "key"})
                self.assertEqual(first["retry_after"], 120)
                self.assertEqual(second["retry_after"], 120)
                self.assertEqual(len(requests), 1)
                sleep.assert_not_awaited()
            self.assertEqual(await limiter.retry_after("/get_last_leaks.php", "other-key"), 0)
            self.assertEqual(await limiter.retry_after("/get_threat_feeds.php", "key"), 0)
            clock[0] += 121
            self.assertEqual(await limiter.retry_after("/get_last_leaks.php", "key"), 0)
        finally:
            await client.aclose()

    async def test_short_retry_still_obeys_local_qps(self):
        clock = [100.0]
        limiter = UpstreamRateLimiter(qps=0.3, clock=lambda: clock[0])
        client = WhiteIntelClient(rate_limiter=limiter)
        sent_at = []
        async def sleep(seconds):
            clock[0] += seconds
        def handler(request):
            sent_at.append(clock[0])
            return httpx.Response(429, headers={"Retry-After": "1"}, json={"error": "Slow down."}) if len(sent_at) == 1 else httpx.Response(200, json={"success": True})
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            with patch("whiteintel_mcp.services.whiteintel_client.asyncio.sleep", side_effect=sleep):
                result = await client.call("last_leaks", {"apikey": "key"})
            self.assertTrue(result["success"])
            self.assertEqual(len(sent_at), 2)
            self.assertGreaterEqual(sent_at[1] - sent_at[0] + 1e-9, 1 / 0.3)
        finally:
            await client.aclose()

    async def test_queued_request_rechecks_new_provider_cooldown(self):
        clock = [100.0]
        limiter = UpstreamRateLimiter(qps=1, clock=lambda: clock[0])
        await limiter.wait("route", "key")
        async def sleep(seconds):
            await limiter.defer("route", "key", 120)
            clock[0] += seconds
        with patch("whiteintel_mcp.services.upstream_rate_limiter.asyncio.sleep", side_effect=sleep):
            with self.assertRaises(RateLimitWaitExceeded) as error:
                await limiter.wait("route", "key", max_wait_seconds=30)
        self.assertEqual(error.exception.retry_after, 119)

    async def test_concurrent_calls_are_spaced(self):
        clock = [100.0]
        limiter = UpstreamRateLimiter(qps=1, clock=lambda: clock[0])
        sent_at = []
        original_sleep = asyncio.sleep
        async def sleep(seconds):
            clock[0] += seconds
            await original_sleep(0)
        async def request():
            await limiter.wait("route", "key")
            sent_at.append(clock[0])
        with patch("whiteintel_mcp.services.upstream_rate_limiter.asyncio.sleep", side_effect=sleep):
            await asyncio.gather(request(), request(), request())
        self.assertEqual(sent_at, [100, 101, 102])

    def test_retry_after_dates_and_invalid_values(self):
        with patch("whiteintel_mcp.services.whiteintel_client.datetime") as mocked:
            mocked.now.return_value = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
            self.assertEqual(_retry_delay_seconds({"retry_after": "Thu, 15 Oct 2026 12:02:00 GMT"}), 120)
        for value in ("nan", "inf", "-1", "invalid"):
            with self.subTest(value=value):
                self.assertEqual(_retry_delay_seconds({"retry_after": value}), 5)

if __name__ == "__main__":
    unittest.main()
