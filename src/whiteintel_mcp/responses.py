"""Page metadata and bounded, identical text/structured MCP responses."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from mcp.types import CallToolResult, TextContent

from whiteintel_mcp.models.responses import WhiteIntelResponse


MAX_OUTPUT_BYTES = 65536
MAX_STRING_CHARS = 4096
_RECORD_KEYS = ("results", "items", "records", "list", "suppliers", "logs", "data")


def record_container(value: object, path: tuple[str, ...] = ()):
    """Find a documented collection, including leaks_by_id's ID-keyed object."""
    if isinstance(value, list):
        return value, path, "list"
    if isinstance(value, dict):
        for key in _RECORD_KEYS:
            child = value.get(key)
            if isinstance(child, list):
                return child, (*path, key), "list"
            if isinstance(child, dict):
                if key == "results" and "compromised_credentials" in child:
                    return [child], (*path, key), "single"
                if key == "results" and child and all(
                    str(name).isdecimal() and isinstance(item, dict)
                    for name, item in child.items()
                ):
                    return child, (*path, key), "mapping"
                found = record_container(child, (*path, key))
                if found is not None:
                    return found
    return None


def count_result_records(value: object) -> int:
    container = record_container(value)
    return len(container[0]) if container is not None else 0


def bounded_response_payload(result: dict[str, Any], request_body: dict[str, Any]) -> dict[str, Any]:
    """Infer continuation only from consistent page metadata and a known position."""
    payload = dict(result)
    container = record_container(payload)
    returned = len(container[0]) if container is not None else 0
    totals, flags = set(), set()
    queue = [payload]
    while queue:
        candidate = queue.pop(0)
        for key in ("total", "total_count", "totalCount"):
            value = candidate.get(key)
            if type(value) is int and value >= 0:
                totals.add(value)
        for key in ("has_more", "hasNextPage", "has_next", "hasMore"):
            value = candidate.get(key)
            if isinstance(value, bool):
                flags.add(value)
        for key in ("data", "meta", "pagination"):
            child = candidate.get(key)
            if isinstance(child, dict):
                queue.append(child)

    offset = request_body.get("offset", payload.get("offset"))
    if type(offset) is not int or offset < 0:
        page = request_body.get("page", payload.get("page", 1))
        limit = request_body.get("limit", payload.get("page_size", payload.get("per_page", payload.get("limit"))))
        offset = 0 if page == 1 else (
            (page - 1) * limit
            if type(page) is int and page >= 1 and type(limit) is int and limit > 0
            else None
        )
    inferred = None
    if len(totals) == 1 and offset is not None and container is not None:
        inferred = next(iter(totals)) > offset + returned
    explicit = next(iter(flags)) if len(flags) == 1 else None
    conflict = len(totals) > 1 or len(flags) > 1 or (
        explicit is not None and inferred is not None and explicit != inferred
    )
    has_more = None if conflict else explicit if explicit is not None else inferred
    failed = payload.get("success") is False
    payload.update(returned_count=returned, truncated=has_more is True and not failed)
    if failed:
        payload.update(completeness="unknown", next_action="stop")
    elif has_more is True:
        payload.update(completeness="partial", next_action="call_next_page")
    elif has_more is False:
        payload.update(completeness="complete", next_action="stop")
    else:
        payload.update(completeness="unknown", next_action="unknown")
    return payload


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def bounded_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(payload)
    clipped = 0

    def clip(value):
        nonlocal clipped
        if isinstance(value, str) and len(value) > MAX_STRING_CHARS:
            clipped += 1
            marker = "… [truncated]"
            return value[:MAX_STRING_CHARS - len(marker)] + marker
        if isinstance(value, list):
            return [clip(item) for item in value]
        if isinstance(value, dict):
            return {key: clip(item) for key, item in value.items()}
        return value

    result = clip(result)
    if not clipped and len(render_json(result).encode("utf-8")) <= MAX_OUTPUT_BYTES:
        return result
    container = record_container(result)
    received = len(container[0]) if container is not None else 0
    budget = dict(max_bytes=MAX_OUTPUT_BYTES, max_string_chars=MAX_STRING_CHARS,
                  received_count=received, omitted_records=0, truncated_fields=clipped)
    result["output"] = budget
    result["truncated"] = True
    if result["success"]:
        result.update(completeness="partial", next_action="refine_query")
    else:
        result.update(completeness="unknown", next_action="stop")

    def retain(count: int) -> None:
        if container is None:
            return
        records, path, kind = container
        parent = result
        for key in path[:-1]:
            parent = parent[key]
        if kind == "single":
            parent[path[-1]] = records[0] if count else None
        else:
            parent[path[-1]] = records[:count] if isinstance(records, list) else dict(list(records.items())[:count])
        result["returned_count"] = count
        budget["omitted_records"] = received - count

    def fits() -> bool:
        return len(render_json(result).encode("utf-8")) <= MAX_OUTPUT_BYTES

    if container is not None and not fits():
        low, high = 0, received
        while low < high:
            middle = (low + high + 1) // 2
            retain(middle)
            if fits():
                low = middle
            else:
                high = middle - 1
        retain(low)
    if not fits():
        # Huge non-record objects and keys must also obey the public JSON budget.
        result = {key: result[key] for key in (
            "success", "http_status", "error", "truncated", "completeness", "next_action", "output"
        ) if key in result}
        result["returned_count"] = 0
        budget["omitted_records"] = received
        error = result.get("error")
        if error:
            result["error"] = {key: error[key] for key in ("code", "retryable", "http_status") if key in error}
            result["error"]["message"] = error.get("message", "Upstream failure.")[:512]
            if error.get("retry_after") is not None:
                value = error["retry_after"]
                result["error"]["retry_after"] = value[:256] if isinstance(value, str) else value
    return result


def tool_result(payload: dict[str, Any]) -> CallToolResult:
    public = WhiteIntelResponse.model_validate(payload).model_dump(mode="json", exclude_none=True)
    public = bounded_payload(public)
    # Validate after clipping as well, including fallback responses.
    public = WhiteIntelResponse.model_validate(public).model_dump(mode="json", exclude_none=True)
    return CallToolResult(
        content=[TextContent(type="text", text=render_json(public))],
        structured_content=public,
        is_error=not public["success"],
    )


def compact_schema(value: Any, *, keep_docs: bool = False) -> Any:
    """Remove repeated documentation without weakening validation constraints."""
    if isinstance(value, dict):
        result = {key: compact_schema(item, keep_docs=keep_docs) for key, item in value.items()
                  if keep_docs or key not in {"title", "description", "default"}}
        branches = result.get("anyOf")
        safe_keys = {"type", "minLength", "maxLength", "pattern", "minimum", "maximum",
                     "exclusiveMinimum", "exclusiveMaximum", "items", "minItems", "maxItems",
                     "uniqueItems", "additionalProperties", "properties", "required",
                     "title", "description", "default"}
        if isinstance(branches, list) and len(branches) == 2 and "type" not in result:
            nullable = next((branch for branch in branches if branch == {"type": "null"}), None)
            branch = next((branch for branch in branches if isinstance(branch, dict) and branch.get("type") != "null"), None)
            if nullable is not None and branch and isinstance(branch.get("type"), str) and branch.keys() <= safe_keys:
                result = {**branch, **{key: item for key, item in result.items() if key != "anyOf"},
                          "type": [branch["type"], "null"]}
        return result
    if isinstance(value, list):
        return [compact_schema(item, keep_docs=keep_docs) for item in value]
    return value
