"""Pydantic request models for every WhiteIntel API endpoint.

Each class maps 1:1 to an upstream endpoint.  Field names, defaults,
and constraints match the official WhiteIntel API v2 documentation.
"""

from __future__ import annotations

from ipaddress import ip_address
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from whiteintel_mcp.models.common import (
    ApiKeyMixin,
    DateRangeMixin,
    PaginationMixin,
    PasswordMaskMixin,
    SystemInfoMixin,
    TypeFilterMixin,
)

SourceType = Literal["all", "stealer", "combolist"]
BreachType = Literal["all", "consumer", "corporate"]
ThreatFeedMode = Literal["public_news"]
ThreatFeedTaxonomy = Literal["categories", "industries", "networks"]
OverallMetric = Literal[
    "consumer_count",
    "corporate_count",
    "computer_count",
    "ip_address_count",
    "application_count",
    "third_party_application_count",
    "applications",
    "third_party_applications",
    "consumer_incident_timeline",
    "corporate_incident_timeline",
    "latest_consumer_events",
    "latest_corporate_events",
    "country_stats",
]
WatchlistAction = Literal["list", "add", "remove", "enable", "disable"]
WatchlistEntryType = Literal["domain", "email", "computername", "ip", "keyword", "github_repo"]
WatchlistStatus = Literal["enabled", "disabled"]
SupplierAction = Literal["list", "add", "remove", "delete"]
SupplierStatus = Literal["active", "paused", "archived", "all"]
SupplierTier = Literal["critical", "high", "medium", "low"]
SupplierSort = Literal["score", "recent", "scanned", "name", "added", "updated"]
SortOrder = Literal["asc", "desc"]


class NonEmptyQueryMixin(BaseModel):
    """Shared validation for endpoints that require a non-empty query."""

    query: str = Field(..., description="Endpoint-specific query value.")

    @field_validator("query")
    @classmethod
    def _query_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query cannot be empty.")
        return value


# ---------------------------------------------------------------------------
# Last Leaks
# ---------------------------------------------------------------------------

class _LastLeaksBase(ApiKeyMixin, PaginationMixin, PasswordMaskMixin):
    pass


class LastLeaksRequest(_LastLeaksBase, NonEmptyQueryMixin):
    """Request model for /get_last_leaks.php"""

    query: str = Field(..., description="Target domain or subdomain (e.g. acme.com).")
    days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Look-back window in days (1–30).",
    )
    data_type: SourceType = Field(
        default="all",
        description="Source type filter: 'all', 'stealer', or 'combolist'.",
    )
    breach_type: BreachType = Field(
        default="all",
        description="Breach category filter: 'all', 'consumer', or 'corporate'.",
    )


# ---------------------------------------------------------------------------
# Threat Feed
# ---------------------------------------------------------------------------

class _ThreatFeedBase(ApiKeyMixin, DateRangeMixin):
    pass


class ThreatFeedRequest(_ThreatFeedBase):
    """Request model for /get_threat_feeds.php

    Mode is auto-selected by which parameters are supplied:
    - taxonomy present → taxonomy mode
    - mode='public_news' → public news mode
    - otherwise → posts mode
    """

    limit: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of records to return (1–100).",
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination.",
    )
    mode: ThreatFeedMode | None = Field(
        default=None,
        description="Set to 'public_news' for public news mode.",
    )
    search: str | None = Field(
        default=None,
        description="Free-text search (min 4 characters).",
    )
    category: str | list[str] | None = Field(
        default=None,
        description="Post category filter, up to 2 values.",
    )
    industry: str | list[str] | None = Field(
        default=None,
        description="Victim industry filter, up to 2 values.",
    )
    network: str | list[str] | None = Field(
        default=None,
        description="Network of origin filter.",
    )
    taxonomy: ThreatFeedTaxonomy | None = Field(
        default=None,
        description="Taxonomy mode: 'categories', 'industries', or 'networks'.",
    )

    @field_validator("search")
    @classmethod
    def _search_min_length(cls, value: str | None) -> str | None:
        if value is not None and value.strip() and len(value.strip()) < 4:
            raise ValueError("Search must be at least 4 characters when supplied.")
        return value

    @field_validator("category", "industry")
    @classmethod
    def _max_two_values(cls, value: str | list[str] | None) -> str | list[str] | None:
        if isinstance(value, list) and len(value) > 2:
            raise ValueError("At most 2 values are supported.")
        return value


# ---------------------------------------------------------------------------
# Consumer Leaks
# ---------------------------------------------------------------------------

class _ConsumerLeaksBase(
    ApiKeyMixin, PaginationMixin, DateRangeMixin,
    PasswordMaskMixin, SystemInfoMixin, TypeFilterMixin,
):
    pass


class ConsumerLeaksRequest(_ConsumerLeaksBase, NonEmptyQueryMixin):
    """Request model for /get_consumer_leaks.php"""

    query: str = Field(..., description="Target domain (e.g. example.com).")
    username: str | None = Field(
        default=None,
        description="Exact-match filter on the leaked username.",
    )
    subdomain: str | None = Field(
        default=None,
        description="Full subdomain when targeting a specific host.",
    )


# ---------------------------------------------------------------------------
# Corporate Leaks
# ---------------------------------------------------------------------------

class _CorporateLeaksBase(
    ApiKeyMixin, PaginationMixin, DateRangeMixin,
    PasswordMaskMixin, SystemInfoMixin, TypeFilterMixin,
):
    pass


class CorporateLeaksRequest(_CorporateLeaksBase, NonEmptyQueryMixin):
    """Request model for /get_corporate_leaks.php"""

    query: str = Field(
        ...,
        description="Target corporate domain (e.g. acme.com).",
    )


# ---------------------------------------------------------------------------
# Database Leaks
# ---------------------------------------------------------------------------

class _DatabaseLeaksBase(ApiKeyMixin, PaginationMixin, DateRangeMixin):
    pass


class DatabaseLeaksRequest(_DatabaseLeaksBase, NonEmptyQueryMixin):
    """Request model for /get_third_party_db_leaks.php"""

    query: str = Field(
        ...,
        description="Target corporate domain (e.g. acme.com).",
    )


# ---------------------------------------------------------------------------
# Overall Stats
# ---------------------------------------------------------------------------

class OverallStatsRequest(ApiKeyMixin):
    """Request model for /get_overall_stats.php"""

    query: str = Field(
        ...,
        description="Target domain or subdomain (e.g. acme.com).",
    )
    metric: OverallMetric = Field(
        ...,
        description=(
            "Metric to compute. One of: consumer_count, corporate_count, "
            "computer_count, ip_address_count, application_count, "
            "third_party_application_count, applications, "
            "third_party_applications, consumer_incident_timeline, "
            "corporate_incident_timeline, latest_consumer_events, "
            "latest_corporate_events, country_stats."
        ),
    )


# ---------------------------------------------------------------------------
# IP Leaks
# ---------------------------------------------------------------------------

class _IPLeaksBase(ApiKeyMixin, PaginationMixin, DateRangeMixin, PasswordMaskMixin):
    pass


class IPLeaksRequest(_IPLeaksBase, NonEmptyQueryMixin):
    """Request model for /get_leaks_by_ip.php"""

    query: str = Field(
        ...,
        description="IP address of the target host (IPv4 or IPv6).",
    )

    @field_validator("query")
    @classmethod
    def _query_is_ip(cls, value: str) -> str:
        ip_address(value)
        return value


# ---------------------------------------------------------------------------
# Computer Leaks
# ---------------------------------------------------------------------------

class _ComputerLeaksBase(ApiKeyMixin, PaginationMixin, DateRangeMixin, PasswordMaskMixin):
    pass


class ComputerLeaksRequest(_ComputerLeaksBase, NonEmptyQueryMixin):
    """Request model for /get_leaks_by_computer_name.php"""

    query: str = Field(
        ...,
        description="Hostname of the target machine (exact, case-sensitive).",
    )


# ---------------------------------------------------------------------------
# Username Leaks
# ---------------------------------------------------------------------------

class _UsernameLeaksBase(
    ApiKeyMixin, PaginationMixin, DateRangeMixin,
    PasswordMaskMixin, SystemInfoMixin, TypeFilterMixin,
):
    pass


class UsernameLeaksRequest(_UsernameLeaksBase, NonEmptyQueryMixin):
    """Request model for /get_leaks_by_username.php"""

    query: str = Field(
        ...,
        description="Exact username or email address to search for.",
    )


# ---------------------------------------------------------------------------
# Lookalike Domains
# ---------------------------------------------------------------------------

class _LookalikeDomainsBase(ApiKeyMixin, PaginationMixin):
    pass


class LookalikeDomainsRequest(_LookalikeDomainsBase):
    """Request model for /get_lookalike_domains.php

    When query is empty/omitted, returns organization-wide results.
    When query is supplied, returns lookalikes targeting that watchlist entry.
    """

    query: str | None = Field(
        default=None,
        description=(
            "Watchlist domain to scope results (omit for organization-wide mode)."
        ),
    )


# ---------------------------------------------------------------------------
# Get Leaks By ID
# ---------------------------------------------------------------------------

class LeaksByIDRequest(ApiKeyMixin, PasswordMaskMixin):
    """Request model for /get_leaks_by_id.php

    Supports single-ID lookup (pass an int) or batched lookup
    (pass a list of 1–5 ints).
    """

    query: int | list[int] = Field(
        ...,
        description="Single log ID or list of up to 5 log IDs.",
    )

    @field_validator("query")
    @classmethod
    def _validate_query_ids(cls, value: int | list[int]) -> int | list[int]:
        if isinstance(value, int):
            if value < 1:
                raise ValueError("Query must be an integer greater than or equal to 1.")
            return value
        if not 1 <= len(value) <= 5:
            raise ValueError("You may request between 1 and 5 IDs per request.")
        if any(item < 1 for item in value):
            raise ValueError("Each ID in query array must be greater than or equal to 1.")
        return value


# ---------------------------------------------------------------------------
# Watchlist Manage
# ---------------------------------------------------------------------------

class WatchlistManageRequest(ApiKeyMixin):
    """Request model for /watchlist_manage.php

    The required fields depend on the action:
    - list:  type, status, page, limit are optional filters
    - add:   entry_type, entry are required
    - remove: id is required
    - enable/disable: id is required
    """

    action: WatchlistAction = Field(
        ...,
        description="Action: 'list', 'add', 'remove', 'enable', or 'disable'.",
    )
    entry_type: WatchlistEntryType | None = Field(
        default=None,
        description="Entry type: domain, email, computername, ip, keyword, github_repo.",
    )
    entry: str | None = Field(
        default=None,
        description="The watchlist entry value (required for 'add').",
    )
    id: int | None = Field(
        default=None,
        description="Watchlist item ID (required for remove/enable/disable).",
    )
    type: WatchlistEntryType | None = Field(
        default=None,
        description="Filter by entry_type when listing.",
    )
    status: WatchlistStatus | None = Field(
        default=None,
        description="Filter by status when listing: 'enabled' or 'disabled'.",
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for listing.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Page size for listing.",
    )
    notify_email: str | None = Field(
        default=None,
        description="Notification email address.",
    )
    push_to_slack: int = Field(
        default=0,
        ge=0,
        le=1,
        description="Enable Slack notification push.",
    )
    push_to_jira: int = Field(
        default=0,
        ge=0,
        le=1,
        description="Enable Jira push.",
    )
    include_usernames: int = Field(
        default=0,
        ge=0,
        le=1,
    )
    include_passwords: int = Field(
        default=0,
        ge=0,
        le=1,
    )
    consumer_alerts: int = Field(
        default=0,
        ge=0,
        le=1,
    )
    corporate_alerts: int = Field(
        default=0,
        ge=0,
        le=1,
    )

    @model_validator(mode="after")
    def _validate_action_fields(self):
        if self.action == "add":
            if self.entry_type is None or self.entry is None or not self.entry.strip():
                raise ValueError("entry_type and entry are required for add.")
        elif self.action in {"remove", "enable", "disable"}:
            if self.id is None:
                raise ValueError("id is required for remove, enable, and disable.")
        return self


# ---------------------------------------------------------------------------
# Supplier Security
# ---------------------------------------------------------------------------

class SupplierRequest(ApiKeyMixin):
    """Request model for /supplier_api.php"""

    action: SupplierAction = Field(
        ...,
        description="Action: 'list', 'add', 'remove', or 'delete'.",
    )
    status: SupplierStatus = Field(
        default="active",
        description="List filter: active, paused, archived, or all.",
    )
    tier: SupplierTier | None = Field(
        default=None,
        description="List filter or add metadata: critical, high, medium, or low.",
    )
    search: str | None = Field(
        default=None,
        max_length=253,
        description="Case-insensitive supplier search query.",
    )
    sort: SupplierSort = Field(
        default="score",
        description="List sort key.",
    )
    order: SortOrder = Field(
        default="desc",
        description="List sort direction.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="List page size (1-200).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="List row offset.",
    )
    domain: str | None = Field(
        default=None,
        description="Supplier domain for add/remove.",
    )
    id: int | None = Field(
        default=None,
        ge=1,
        description="Supplier identifier for remove/delete.",
    )
    display_name: str | None = Field(
        default=None,
        max_length=255,
        description="Human-readable supplier name.",
    )
    size: str | None = Field(
        default=None,
        max_length=32,
        description="Organization size label.",
    )
    country: str | None = Field(
        default=None,
        max_length=64,
        description="Country label.",
    )
    industry: str | None = Field(
        default=None,
        max_length=96,
        description="Industry label.",
    )
    category: str | None = Field(
        default=None,
        max_length=64,
        description="Category label.",
    )
    supplier_tier: SupplierTier | None = Field(
        default=None,
        description="Assigned supplier tier.",
    )
    notes: str | None = Field(
        default=None,
        max_length=5000,
        description="Free-form supplier notes.",
    )

    @field_validator("domain")
    @classmethod
    def _domain_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Domain cannot be empty when supplied.")
        return value

    @field_validator(
        "search",
        "display_name",
        "size",
        "country",
        "industry",
        "category",
        "notes",
        mode="before",
    )
    @classmethod
    def _empty_strings_are_absent(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _validate_action_fields(self):
        if self.action == "add" and self.domain is None:
            raise ValueError("domain is required for add.")
        if self.action in {"remove", "delete"} and self.id is None and self.domain is None:
            raise ValueError("id or domain is required for remove/delete.")
        return self


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

class AuditLogsRequest(ApiKeyMixin):
    """Request model for /get_audit_logs.php"""

    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination.",
    )
