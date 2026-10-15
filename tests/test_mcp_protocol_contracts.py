from __future__ import annotations

import json
import os
import unittest
from contextlib import asynccontextmanager
from unittest.mock import patch

import httpx
from jsonschema import Draft202012Validator
from mcp import Client, ClientSession
from mcp.client._memory import InMemoryTransport
from mcp.shared.exceptions import MCPError
from mcp.types import (CallToolResult, TextContent, ClientCapabilities, Implementation, InitializedNotification,
                       InitializeRequest, InitializeRequestParams, InitializeResult)

from whiteintel_mcp.mcp_server import ContractMCPServer, SCHEMA_META_KEY, SCHEMA_URI
from whiteintel_mcp.models.responses import WhiteIntelResponse
from whiteintel_mcp.server import create_server


@asynccontextmanager
async def connect(server, version):
    async with InMemoryTransport(server) as streams:
        async with ClientSession(*streams) as client:
            if version == "2026-07-28":
                discovery = await client.discover()
            else:
                discovery = await client.send_request(InitializeRequest(params=InitializeRequestParams(
                    protocol_version=version, capabilities=ClientCapabilities(),
                    client_info=Implementation(name="whiteintel-tests", version="1"),
                )), InitializeResult)
                client.adopt(discovery)
                await client.send_notification(InitializedNotification())
            yield client, discovery


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"WHITEINTEL_API_KEY": "test-key", "WHITEINTEL_UPSTREAM_QPS": "1000000"}, clear=True)
        self.environment.start()
        self.status = 200
        self.body = {"success": True, "results": [{"id": 1}], "total": 1}
        self.requests = []
        original = httpx.AsyncClient

        def handle(request):
            self.requests.append(json.loads(request.content))
            return httpx.Response(self.status, json=self.body)

        self.http = patch.object(httpx, "AsyncClient", side_effect=lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
        self.http.start()

    def tearDown(self):
        self.http.stop()
        self.environment.stop()

    def check_result(self, result, schema, *, error_code=None):
        payload = result.structured_content
        self.assertIsNotNone(payload)
        self.assertEqual(json.loads(result.content[0].text), payload)
        Draft202012Validator(schema).validate(payload)
        self.assertEqual(result.is_error, error_code is not None)
        if error_code:
            self.assertEqual(payload["error"]["code"], error_code)
            self.assertEqual(payload["next_action"], "stop")
        return payload

    async def test_all_protocol_eras_keep_success_and_failures_structured(self):
        for version in ("2025-03-26", "2025-06-18", "2025-11-25", "2026-07-28"):
            with self.subTest(version=version):
                async with connect(create_server(), version) as (client, discovery):
                    tools = {t.name: t for t in (await client.list_tools()).tools}
                    self.assertEqual(tools["last_leaks"].output_schema, {"type": "object"})
                    resource = await client.read_resource(tools["last_leaks"].meta[SCHEMA_META_KEY])
                    schema = json.loads(resource.contents[0].text)
                    self.assertEqual(schema, WhiteIntelResponse.model_json_schema(mode="serialization"))
                    Draft202012Validator.check_schema(schema)
                    self.assertEqual(len(tools), 16)
                    modern = version == "2026-07-28"
                    self.assertEqual(discovery.capabilities.resources.subscribe, modern)
                    self.assertEqual(discovery.capabilities.tools.list_changed, modern)
                    self.assertIsNone(discovery.capabilities.logging)
                    if modern:
                        self.assertEqual(discovery.supported_versions, [version])
                        with self.assertRaises(MCPError) as error:
                            await client.send_discover("2099-01-01")
                        self.assertEqual(error.exception.code, -32022)
                    else:
                        self.assertEqual(discovery.protocol_version, version)
                    self.status, self.body = 200, {"success": True, "results": [{"id": 1}], "total": 1}
                    payload = self.check_result(await client.call_tool("last_leaks", {"query": "example.test", "limit": 1}), schema)
                    self.assertEqual((payload["returned_count"], payload["next_action"]), (1, "stop"))
                    for name, arguments, code in (
                        ("last_leaks", {}, "INVALID_REQUEST"),
                        ("last_leaks", {"query": "example.test", "limit": 99999}, "INVALID_REQUEST"),
                        ("consumer_leaks", {"query": "example.test", "start_date": "2026-01-01"}, "INVALID_REQUEST"),
                        ("consumer_leaks", {"query": "example.test", "start_date": "2026-02-30", "end_date": "2026-03-01"}, "INVALID_REQUEST"),
                        ("leaks_by_id", {"query": [1, 2, 3, 4, 5, 6]}, "INVALID_REQUEST"),
                        ("card_check", {"bin": "1234567"}, "INVALID_REQUEST"),
                        ("card_check", {"bin": "424242", "country": "US"}, "INVALID_REQUEST"),
                        ("last_leaks", {"query": "example.test", "bogus": 1}, "INVALID_REQUEST"),
                        ("unknown_tool", {}, "TOOL_NOT_FOUND"),
                    ):
                        before = len(self.requests)
                        payload = self.check_result(await client.call_tool(name, arguments), schema, error_code=code)
                        self.assertEqual(len(self.requests), before)
                        self.assertNotIn('"input"', json.dumps(payload))
                        self.assertNotIn("test-key", json.dumps(payload))
                        if name == "consumer_leaks":
                            self.assertTrue(payload["error"]["validation_errors"])
                    for status, body, code in (
                        (200, {"success": False, "message": "Daily API request limit exceeded."}, "QUOTA_EXHAUSTED"),
                        (403, {"error": "API Key is missing."}, "AUTH_INVALID"),
                        (200, {}, "UPSTREAM_ERROR"),
                        (200, {"error": "Invalid request."}, "UPSTREAM_ERROR"),
                        (500, {"success": True, "results": []}, "UPSTREAM_UNAVAILABLE"),
                    ):
                        self.status, self.body = status, body
                        self.check_result(await client.call_tool("last_leaks", {"query": "example.test"}), schema, error_code=code)

    async def test_all_tools_publish_strict_valid_schemas(self):
        tools = {t.name: t for t in await create_server(enable_write_tools=True).list_tools()}
        self.assertEqual(len(tools), 23)
        for tool in tools.values():
            self.assertTrue(tool.title and tool.annotations and tool.output_schema)
            self.assertEqual(tool.output_schema, {"type": "object"})
            self.assertEqual(tool.meta[SCHEMA_META_KEY], SCHEMA_URI)
            self.assertFalse(tool.input_schema["additionalProperties"])
            self.assertNotIn("apikey", tool.input_schema["properties"])
            Draft202012Validator.check_schema(tool.input_schema)
            Draft202012Validator.check_schema(tool.output_schema)
        for name, arguments, valid in (
            ("leaks_by_id", {"query": [1, 2, 3, 4, 5]}, True),
            ("leaks_by_id", {"query": [1, 2, 3, 4, 5, 6]}, False),
            ("leaks_by_id", {"query": []}, False),
            ("leaks_by_id", {"query": 0}, False),
            ("card_check", {"bin": "424242"}, True),
            ("card_check", {"bin": "42424200"}, True),
            ("card_check", {"bin": "4242420"}, False),
            ("card_check", {"issuer": "Example Bank"}, True),
            ("card_check", {}, False),
            ("card_check", {"bin": "424242", "country": "US"}, False),
            ("consumer_leaks", {"query": "example.test", "start_date": "2026-01-01"}, False),
            ("consumer_leaks", {"query": "example.test", "start_date": "2026-01-01", "end_date": None}, False),
            ("consumer_leaks", {"query": "example.test", "start_date": None, "end_date": None}, True),
            ("threat_feed", {"start_date": "2026-01-01"}, True),
            ("threat_feed_darkweb_chatters", {"end_date": "2026-01-01"}, True),
            ("last_leaks", {"query": "example.test", "bogus": 1}, False),
        ):
            with self.subTest(name=name, arguments=arguments):
                self.assertEqual(Draft202012Validator(tools[name].input_schema).is_valid(arguments), valid)

    async def test_static_methods_have_private_cache_hints_and_schema_resource(self):
        async with connect(create_server(), "2026-07-28") as (client, discovery):
            results = [discovery, await client.list_tools(), await client.list_resources(),
                       await client.list_resource_templates(), await client.list_prompts(),
                       await client.read_resource("whiteintel://docs/last-leaks-api.md")]
            for result in results:
                self.assertGreater(result.ttl_ms, 0)
                self.assertEqual(result.cache_scope, "private")
            response = await client.read_resource(SCHEMA_URI)
            schema = json.loads(response.contents[0].text)
            self.assertEqual(schema, WhiteIntelResponse.model_json_schema(mode="serialization"))

    async def test_catalog_size_stays_within_context_budget(self):
        for writes, count, max_bytes in ((False, 16, 40_000), (True, 23, 50_000)):
            with self.subTest(write_tools=writes):
                tools = await create_server(enable_write_tools=writes).list_tools()
                self.assertEqual(len(tools), count)
                serialized = json.dumps([
                    tool.model_dump(mode="json", by_alias=True, exclude_none=True) for tool in tools
                ]).encode("utf-8")
                self.assertLess(len(serialized), max_bytes)
                for tool in tools:
                    self.assertEqual(tool.output_schema, {"type": "object"})

    async def test_schema_link_preserves_existing_vendor_metadata(self):
        server = ContractMCPServer("metadata-test")

        @server.tool(meta={"example/label": "kept"})
        def local() -> WhiteIntelResponse:
            return WhiteIntelResponse(success=True, http_status=200)

        tool = (await server.list_tools())[0]
        self.assertEqual(tool.meta["example/label"], "kept")
        self.assertEqual(tool.model_dump(mode="json", by_alias=True)["_meta"][SCHEMA_META_KEY], SCHEMA_URI)

    async def test_public_catalog_reflects_tool_add_remove_and_replacement(self):
        server = ContractMCPServer("dynamic-test")

        def initial(query: str) -> WhiteIntelResponse:
            return WhiteIntelResponse(success=True, http_status=200, value=query)

        server.add_tool(initial, name="dynamic")
        result = await server.call_tool("dynamic", {"query": "first"})
        self.assertEqual(result.structured_content["value"], "first")
        server.remove_tool("dynamic")
        missing = await server.call_tool("dynamic", {})
        self.assertTrue(missing.is_error)
        self.assertEqual(missing.structured_content["error"]["code"], "TOOL_NOT_FOUND")

        def replacement(limit: int) -> WhiteIntelResponse:
            return WhiteIntelResponse(success=True, http_status=200, value=limit)

        server.add_tool(replacement, name="dynamic")
        rejected = await server.call_tool("dynamic", {"query": "old"})
        self.assertTrue(rejected.is_error)
        self.assertEqual(rejected.structured_content["error"]["code"], "INVALID_REQUEST")
        result = await server.call_tool("dynamic", {"limit": 2})
        self.assertFalse(result.is_error)
        self.assertEqual(result.structured_content["value"], 2)

    async def test_modern_subscriptions_are_acknowledged(self):
        async with Client(create_server(), cache=None, read_timeout_seconds=5) as client:
            async with client.listen(tools_list_changed=True, resource_subscriptions=[SCHEMA_URI]) as sub:
                self.assertTrue(sub.honored.tools_list_changed)
                self.assertEqual(sub.honored.resource_subscriptions, [SCHEMA_URI])

    async def test_protocol_errors_remain_protocol_errors(self):
        server = ContractMCPServer("protocol-error-test")

        @server.tool()
        def protocol_error() -> WhiteIntelResponse:
            raise MCPError(-32602, "Protocol-level error")

        async with connect(server, "2026-07-28") as (client, _):
            with self.assertRaises(MCPError) as error:
                await client.call_tool("protocol_error", {})
            self.assertEqual(error.exception.code, -32602)

    async def test_unexpected_crash_is_structured_without_exception_details(self):
        server = ContractMCPServer("crash-test")

        @server.tool()
        def crash() -> WhiteIntelResponse:
            raise RuntimeError("private exception details")

        with self.assertLogs("whiteintel_mcp.mcp_server", level="ERROR"):
            result = await server.call_tool("crash", {})
        self.assertTrue(result.is_error)
        self.assertEqual(result.structured_content["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("private exception details", result.content[0].text)

    async def test_result_serialization_failure_stays_structured(self):
        server = ContractMCPServer("serialization-test")

        @server.tool()
        def malformed_result() -> CallToolResult:
            return CallToolResult(content=[TextContent(type="text", text="{}")],
                                  structured_content={"success": True})

        with self.assertLogs("whiteintel_mcp.mcp_server", level="ERROR"):
            result = await server.call_tool("malformed_result", {})
        self.assertTrue(result.is_error)
        self.assertEqual(result.structured_content["error"]["code"], "INTERNAL_ERROR")
        self.assertEqual(json.loads(result.content[0].text), result.structured_content)

    async def test_missing_server_key_is_an_actionable_structured_failure(self):
        with patch.dict(os.environ, {"WHITEINTEL_API_KEY": ""}):
            async with connect(create_server(), "2026-07-28") as (client, _):
                result = await client.call_tool("last_leaks", {"query": "example.test"})
                self.assertEqual(result.structured_content["error"]["code"], "AUTH_INVALID")
                self.assertTrue(result.is_error)
                self.assertFalse(self.requests)


if __name__ == "__main__":
    unittest.main()
