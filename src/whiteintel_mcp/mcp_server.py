"""SDK 2.3 integration for strict input and uniform execution results."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server import CacheHint, MCPServer
from mcp.server.mcpserver.exceptions import ToolError, UnexpectedToolError
from mcp.shared.exceptions import MCPError
from mcp.types import CallToolResult
from pydantic import ValidationError

from whiteintel_mcp.models.responses import WhiteIntelResponse
from whiteintel_mcp.responses import compact_schema, render_json, tool_result


SCHEMA_URI = "whiteintel://schemas/response"
SCHEMA_META_KEY = "whiteintel/outputSchema"
_LOGGER = logging.getLogger(__name__)
DEFAULT_CACHE_HINTS = {
    method: CacheHint(ttl_ms=300_000, scope="private")
    for method in ("tools/list", "server/discover", "prompts/list", "resources/list", "resources/templates/list")
}
DEFAULT_CACHE_HINTS["resources/read"] = CacheHint(ttl_ms=3_600_000, scope="private")


def local_error(code: str, message: str, status: int = 400, **details: Any) -> CallToolResult:
    return tool_result({
        "success": False, "http_status": status,
        "error": {"code": code, "message": message, "retryable": False, **details},
        "next_action": "stop",
    })


class ContractMCPServer(MCPServer):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["cache_hints"] = {**DEFAULT_CACHE_HINTS, **(kwargs.get("cache_hints") or {})}
        kwargs.setdefault("website_url", "https://github.com/helGayhub233/WhiteIntel-MCP")
        super().__init__(*args, **kwargs)

        @self.resource(SCHEMA_URI, name="response-schema", title="WhiteIntel Response Schema",
                       description="Full field documentation for the shared tool response.",
                       mime_type="application/schema+json")
        def response_schema() -> str:
            return render_json(WhiteIntelResponse.model_json_schema(mode="serialization"))

    async def list_tools(self):
        tools = []
        for tool in await super().list_tools():
            input_schema = {**compact_schema(tool.input_schema, keep_docs=True), "additionalProperties": False}
            properties = input_schema.get("properties", {})
            if {"start_date", "end_date"} <= properties.keys() and tool.name not in {
                "threat_feed", "threat_feed_darkweb_chatters"
            }:
                input_schema["allOf"] = [
                    {"if": {"required": [first], "properties": {first: {"type": "string"}}},
                     "then": {"required": [second], "properties": {second: {"type": "string"}}}}
                    for first, second in (("start_date", "end_date"), ("end_date", "start_date"))
                ]
            tools.append(tool.model_copy(update={
                "input_schema": input_schema,
                "output_schema": {"type": "object"},
                "meta": {**(tool.meta or {}), SCHEMA_META_KEY: SCHEMA_URI},
            }))
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any], context: Any = None):
        # Use the SDK's public catalog, reflecting add_tool/remove_tool immediately.
        tool = next((tool for tool in await super().list_tools() if tool.name == name), None)
        if tool is None:
            return local_error("TOOL_NOT_FOUND", "Unknown tool. Select an available tool using tools/list.", 404)
        schema = tool.input_schema
        extra = sorted(arguments.keys() - schema.get("properties", {}).keys())
        if extra:
            return local_error("INVALID_REQUEST", "Unexpected tool arguments.", validation_errors=[
                {"loc": [key], "type": "extra_forbidden", "message": "Extra inputs are not permitted"}
                for key in extra
            ])
        try:
            result = await super().call_tool(name, arguments, context)
            if isinstance(result, CallToolResult) and result.structured_content is not None:
                return tool_result(result.structured_content)
            return result
        except MCPError:
            raise
        except ToolError as exc:
            cause = exc.__cause__
            while isinstance(cause, ToolError) and cause.__cause__ is not None:
                cause = cause.__cause__
            if isinstance(cause, ValidationError):
                errors = cause.errors(include_input=False, include_context=False, include_url=False)
                if any("apikey" in item["loc"] for item in errors):
                    return local_error("AUTH_INVALID", "Configure WHITEINTEL_API_KEY on the server.", 401)
                return local_error("INVALID_REQUEST", "Invalid tool arguments. Correct the listed fields.",
                                   validation_errors=[
                                       {"loc": list(item["loc"]), "type": item["type"], "message": item["msg"]}
                                       for item in errors
                                   ])
            if isinstance(exc, UnexpectedToolError):
                _LOGGER.exception("Tool %r failed unexpectedly", name)
                return local_error("INTERNAL_ERROR", "Tool execution failed unexpectedly. Inspect server logs.", 500)
            return local_error("UPSTREAM_ERROR", "Tool execution failed. Inspect server logs.", 502)
        except Exception:
            _LOGGER.exception("Tool %r result could not be normalized", name)
            return local_error("INTERNAL_ERROR", "Tool response could not be serialized. Inspect server logs.", 500)
