"""Stable MCP-facing response envelope for WhiteIntel tools."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from whiteintel_mcp.tool_errors import ToolErrorCode


class WhiteIntelError(BaseModel):
    """Machine-readable failure without rejected argument values or API credentials."""

    code: ToolErrorCode
    message: str
    retryable: bool = False
    http_status: int | None = None
    retry_after: float | str | None = None
    validation_errors: list[dict[str, Any]] | None = None


class OutputBudget(BaseModel):
    max_bytes: int
    max_string_chars: int
    received_count: int
    omitted_records: int
    truncated_fields: int


class WhiteIntelResponse(BaseModel):
    """Preserve upstream data while documenting fields shared by most endpoints."""

    model_config = ConfigDict(extra="allow")

    success: bool = Field(description="Whether the WhiteIntel operation succeeded.")
    http_status: int = Field(ge=100, le=599, description="WhiteIntel HTTP status code.")
    message: str | None = Field(default=None, description="Optional upstream status message.")
    error: WhiteIntelError | None = None
    output: OutputBudget | None = None
    remaining_daily_calls: int | None = Field(
        default=None,
        ge=0,
        description="Remaining calls in the standard daily quota, when reported.",
    )
    remaining_threat_feed_calls: int | None = Field(
        default=None,
        ge=0,
        description="Remaining Threat Feed calls, when reported.",
    )
    returned_count: int = Field(
        default=0,
        ge=0,
        description="Number of records returned in this response page when detectable.",
    )
    truncated: bool = Field(
        default=False,
        description="Whether the provider has more records or local output clipping occurred.",
    )
    completeness: Literal["complete", "partial", "unknown"] = Field(
        default="unknown",
        description="Whether this response is complete, partial, or unknown.",
    )
    next_action: Literal["stop", "call_next_page", "refine_query", "unknown"] = Field(
        default="unknown",
        description="refine_query means reduce page size or narrow the query before paging; stop on failures.",
    )

    def extra_data(self) -> dict[str, Any]:
        """Return endpoint-specific fields retained by Pydantic's extra policy."""
        return self.model_extra or {}
