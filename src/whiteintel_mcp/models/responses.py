"""Stable MCP-facing response envelope for WhiteIntel tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WhiteIntelResponse(BaseModel):
    """Preserve upstream data while documenting fields shared by most endpoints."""

    model_config = ConfigDict(extra="allow")

    success: bool = Field(description="Whether the WhiteIntel operation succeeded.")
    http_status: int = Field(ge=100, le=599, description="WhiteIntel HTTP status code.")
    message: str | None = Field(default=None, description="Optional upstream status message.")
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

    def extra_data(self) -> dict[str, Any]:
        """Return endpoint-specific fields retained by Pydantic's extra policy."""
        return self.model_extra or {}
