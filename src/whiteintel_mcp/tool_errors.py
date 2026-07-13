"""Translate WhiteIntel failures into actionable MCP tool errors."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError


class ToolErrorCode(str, Enum):
    AUTH_INVALID = "AUTH_INVALID"
    ENTITLEMENT_REQUIRED = "ENTITLEMENT_REQUIRED"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_REQUEST = "INVALID_REQUEST"
    FORBIDDEN = "FORBIDDEN"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"


_QUOTA_MARKERS = ("quota", "daily limit", "request limit", "credit allowance")
_ENTITLEMENT_MARKERS = (
    "add-on",
    "addon",
    "license",
    "subscription",
    "tier",
    "upgrade",
    "not available",
    "only available",
)


def _message(result: dict[str, Any]) -> str:
    for key in ("error", "message", "detail"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "WhiteIntel rejected the tool request."


def classify_error(result: dict[str, Any]) -> ToolErrorCode:
    """Classify HTTP and HTTP-200 business failures without conflating quota and access."""
    status = result.get("http_status")
    message = _message(result).lower()

    if status == 401 or "invalid api key" in message or "missing api key" in message:
        return ToolErrorCode.AUTH_INVALID
    if status == 429 or "too many requests" in message or "rate limit" in message:
        return ToolErrorCode.RATE_LIMITED
    if any(marker in message for marker in _QUOTA_MARKERS):
        return ToolErrorCode.QUOTA_EXHAUSTED
    if any(marker in message for marker in _ENTITLEMENT_MARKERS):
        return ToolErrorCode.ENTITLEMENT_REQUIRED
    if status == 403:
        return ToolErrorCode.FORBIDDEN
    if status == 400 or "validation" in message or "invalid parameter" in message:
        return ToolErrorCode.INVALID_REQUEST
    if isinstance(status, int) and status >= 500:
        return ToolErrorCode.UPSTREAM_UNAVAILABLE
    return ToolErrorCode.UPSTREAM_ERROR


def to_tool_error(result: dict[str, Any]) -> ToolError:
    """Build a machine-readable error that FastMCP emits with ``isError=true``."""
    code = classify_error(result)
    payload: dict[str, Any] = {
        "code": code.value,
        "message": _message(result),
        "http_status": result.get("http_status"),
        "retryable": code in {ToolErrorCode.RATE_LIMITED, ToolErrorCode.UPSTREAM_UNAVAILABLE},
    }
    if result.get("retry_after") is not None:
        payload["retry_after"] = result["retry_after"]
    return ToolError(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
