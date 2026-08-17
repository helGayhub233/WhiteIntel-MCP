from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from whiteintel_mcp.models.endpoints import (
    CardCheckRequest,
    ConsumerLeaksRequest,
    ThreatFeedRequest,
)
from whiteintel_mcp.services.upstream_rate_limiter import (
    DEFAULT_QPS,
    UpstreamRateLimiter,
    qps_from_environment,
)
from whiteintel_mcp.server import create_server
from whiteintel_mcp.tool_errors import ToolErrorCode, classify_error


class RequestContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = patch.dict(os.environ, {"WHITEINTEL_API_KEY": "test-key"})
        self.api_key.start()

    def tearDown(self) -> None:
        self.api_key.stop()

    def test_threat_feed_accepts_independent_date_bounds(self) -> None:
        request = ThreatFeedRequest(apikey="", start_date="2026-01-01")
        self.assertEqual(request.start_date, "2026-01-01")
        self.assertIsNone(request.end_date)

    def test_other_leak_date_ranges_remain_paired(self) -> None:
        with self.assertRaises(ValidationError):
            ConsumerLeaksRequest(
                apikey="",
                query="example.com",
                start_date="2026-01-01",
            )

    def test_card_contract_matches_documented_selectors_and_filters(self) -> None:
        request = CardCheckRequest(
            apikey="",
            country="United States",
            countries=["US", "CA"],
            valid_only=True,
        )
        body = request.model_dump(exclude_none=True)
        self.assertEqual(body["country"], "United States")
        self.assertEqual(body["countries"], ["US", "CA"])
        self.assertIs(body["valid_only"], True)

    def test_card_issuer_and_country_filter_constraints(self) -> None:
        with self.assertRaises(ValidationError):
            CardCheckRequest(apikey="", issuer="AB")
        with self.assertRaises(ValidationError):
            CardCheckRequest(apikey="", country="US", countries=["usa"])

    def test_card_exposure_dates_must_be_ordered(self) -> None:
        with self.assertRaises(ValidationError):
            CardCheckRequest(
                apikey="",
                bin="424242",
                exposed_after="2026-02-01",
                exposed_before="2026-01-01",
            )


class ErrorClassificationTests(unittest.TestCase):
    def test_documented_missing_api_key_shape(self) -> None:
        result = {"http_status": 403, "error": "API Key is missing."}
        self.assertEqual(classify_error(result), ToolErrorCode.AUTH_INVALID)

    def test_http_200_validation_shapes(self) -> None:
        examples = (
            "Limit must be between 1 and 100.",
            "Provide exactly one primary selector: bin, issuer, or country.",
            "Query can not be empty.",
        )
        for message in examples:
            with self.subTest(message=message):
                self.assertEqual(
                    classify_error({"http_status": 200, "error": message}),
                    ToolErrorCode.INVALID_REQUEST,
                )

    def test_http_200_quota_precedes_generic_validation(self) -> None:
        result = {
            "http_status": 200,
            "message": "Daily payment fraud API request limit exceeded.",
        }
        self.assertEqual(classify_error(result), ToolErrorCode.QUOTA_EXHAUSTED)


class RateConfigurationTests(unittest.TestCase):
    def test_default_and_configured_qps(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(qps_from_environment(), DEFAULT_QPS)
        with patch.dict(os.environ, {"WHITEINTEL_UPSTREAM_QPS": "1.5"}):
            limiter = UpstreamRateLimiter.from_environment()
            self.assertEqual(limiter.qps, 1.5)

    def test_invalid_qps_fails_closed(self) -> None:
        for value in ("0", "-1", "nan", "not-a-number"):
            with self.subTest(value=value):
                with patch.dict(os.environ, {"WHITEINTEL_UPSTREAM_QPS": value}):
                    with self.assertRaises(ValueError):
                        qps_from_environment()


class PublishedToolSchemaTests(unittest.IsolatedAsyncioTestCase):
    async def test_default_tool_surface_exposes_current_contract(self) -> None:
        with patch.dict(os.environ, {"WHITEINTEL_API_KEY": "test-key"}):
            tools = {tool.name: tool for tool in await create_server().list_tools()}

        self.assertEqual(len(tools), 16)
        card = tools["card_check"].input_schema
        threat_feed = tools["threat_feed"].input_schema
        self.assertIn("countries", card["properties"])
        self.assertEqual(
            card["properties"]["issuer"]["anyOf"][0]["minLength"], 3
        )
        self.assertEqual(
            card["properties"]["country"]["anyOf"][0]["maxLength"], 100
        )
        self.assertTrue(
            threat_feed["properties"]["start_date"]["description"].startswith(
                "Optional inclusive"
            )
        )
