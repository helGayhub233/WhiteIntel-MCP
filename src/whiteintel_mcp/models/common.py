"""Shared Pydantic field mixins for WhiteIntel API request models."""

from __future__ import annotations

import os
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SourceType = Literal["all", "stealer", "combolist"]
UsernameSourceType = Literal["all", "stealer", "combolist", "database"]
LeakIds = Annotated[int, Field(ge=1)] | Annotated[list[Annotated[int, Field(ge=1)]], Field(min_length=1, max_length=5)]


class ApiKeyMixin(BaseModel):
    """Every WhiteIntel API request requires an API key in the body."""

    model_config = ConfigDict(extra="forbid")

    apikey: str = Field(
        ...,
        description="Your Whiteintel API key from the Organizations or Profile page.",
    )

    @field_validator("apikey")
    @classmethod
    def _apikey_not_empty(cls, value: str) -> str:
        if value.strip():
            return value
        env_value = os.getenv("WHITEINTEL_API_KEY", "").strip()
        if env_value:
            return env_value
        if not value.strip():
            raise ValueError("API key cannot be empty.")
        return value


class PaginationMixin(BaseModel):
    """Pagination parameters shared by list-style endpoints."""

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return per page (1–1000). Default interactive page is 100; request larger collections through pagination.",
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination.",
    )


class DateRangeMixin(BaseModel):
    """Optional date-range filter (both must be supplied together when used)."""

    start_date: str | None = Field(
        default=None,
        pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
        description="Lower bound of date range, format YYYY-MM-DD.",
    )
    end_date: str | None = Field(
        default=None,
        pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
        description="Upper bound of date range, format YYYY-MM-DD.",
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def _date_is_iso(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Date must use YYYY-MM-DD format.") from exc
        return value

    @model_validator(mode="after")
    def _dates_are_paired(self):
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("Both start_date and end_date must be provided together.")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be earlier than or equal to end_date.")
        return self


class IndependentDateBoundsMixin(BaseModel):
    """Optional ISO date bounds that may be supplied independently."""

    start_date: str | None = Field(
        default=None,
        pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
        description="Optional inclusive lower bound, format YYYY-MM-DD.",
    )
    end_date: str | None = Field(
        default=None,
        pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
        description="Optional inclusive upper bound, format YYYY-MM-DD.",
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def _date_is_iso(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Date must use YYYY-MM-DD format.") from exc
        return value

    @model_validator(mode="after")
    def _dates_are_ordered(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be earlier than or equal to end_date.")
        return self


class PasswordMaskMixin(BaseModel):
    """Control whether plaintext passwords are returned."""

    mask_password: int = Field(
        default=0,
        ge=0,
        le=1,
        description="Set to 1 to omit the password field from results.",
    )


class SystemInfoMixin(BaseModel):
    """Control whether stealer records include host-level system information."""

    include_system_info: int = Field(
        default=0,
        ge=0,
        le=1,
        description="Set to 1 to include hostname, IP, malware_path, anti_virus.",
    )


class DataTypeMixin(BaseModel):
    """Filter by data source type."""

    data_type: SourceType = Field(
        default="all",
        description="Source type filter: 'all', 'stealer', or 'combolist'.",
    )


# Aliases for endpoints that use 'type' instead of 'data_type'.

class TypeFilterMixin(BaseModel):
    """Filter by source type (used by consumer_leaks, corporate_leaks, username_leaks)."""

    type: SourceType = Field(
        default="all",
        description="Result source type: 'all', 'stealer', or 'combolist'.",
    )
