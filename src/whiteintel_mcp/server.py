"""MCP server for WhiteIntel threat intelligence APIs."""

from __future__ import annotations

import argparse
import os
from contextlib import asynccontextmanager
from ipaddress import ip_address
from pathlib import Path
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from whiteintel_mcp import __version__
from whiteintel_mcp.models.endpoints import (
    AuditLogsRequest,
    BreachType,
    CardCheckSortBy,
    CardCheckSortDir,
    CardCheckRequest,
    ComputerLeaksRequest,
    ConsumerLeaksRequest,
    CorporateLeaksRequest,
    DarkwebChattersRequest,
    DatabaseLeaksRequest,
    IPLeaksRequest,
    LastLeaksRequest,
    LeaksByIDRequest,
    LookalikeDomainsRequest,
    OverallStatsRequest,
    OverallMetric,
    SortOrder,
    SourceType,
    SupplierSort,
    SupplierStatus,
    SupplierTier,
    SupplierRequest,
    ThreatFeedRequest,
    ThreatFeedMode,
    ThreatFeedTaxonomy,
    UsernameLeaksRequest,
    WatchlistEntryType,
    WatchlistManageRequest,
    WatchlistStatus,
)
from whiteintel_mcp.models.responses import WhiteIntelResponse
from whiteintel_mcp.services.upstream_rate_limiter import UpstreamRateLimiter
from whiteintel_mcp.services.whiteintel_client import WhiteIntelClient
from whiteintel_mcp.tool_errors import to_tool_error
from whiteintel_mcp.tool_policy import ToolPolicy, env_flag


SERVER_INSTRUCTIONS = (
    "This server exposes WhiteIntel threat intelligence tools for credential exposure, "
    "threat feeds, database leaks, lookalike domains, watchlist management, supplier "
    "security, card check, and audit logs. The API key is read from the "
    "WHITEINTEL_API_KEY server environment variable."
)

READ_ONLY_TOOL = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)
MUTATING_TOOL = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=True,
)
IDEMPOTENT_MUTATION_TOOL = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)
DESTRUCTIVE_TOOL = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=False,
    open_world_hint=True,
)

PositiveInt = Annotated[
    int,
    Field(ge=1, description="One-based results page."),
]
NonNegativeInt = Annotated[
    int,
    Field(ge=0, description="Zero-based offset into the result set."),
]
BinaryInt = Annotated[
    int,
    Field(ge=0, le=1, description="Binary option: 1 enables the named behavior and 0 disables it."),
]
Days = Annotated[
    int,
    Field(ge=1, le=30, description="Lookback window in whole days, from 1 through 30."),
]
Limit100 = Annotated[
    int,
    Field(ge=1, le=100, description="Maximum records requested, from 1 through 100."),
]
Limit200 = Annotated[
    int,
    Field(ge=1, le=200, description="Maximum records requested, from 1 through 200."),
]
Limit5000 = Annotated[
    int,
    Field(ge=1, le=5000, description="Maximum records requested, from 1 through 5000."),
]
OptionalCardBin = Annotated[
    str | None,
    Field(
        min_length=6,
        max_length=8,
        pattern=r"^\d{6,8}$",
        description="Optional six- to eight-digit card issuer identification number.",
    ),
]

WHITEINTEL_RATE_DISCLOSURE = (
    " Requires WHITEINTEL_API_KEY; requests use conservative local pacing per "
    "upstream route and API key (default 0.2 QPS, configurable with "
    "WHITEINTEL_UPSTREAM_QPS) before provider-directed cooldowns are applied."
)


class WhiteIntelMCPServer(MCPServer):
    """Expose shared remote behavior and cross-field constraints to MCP clients."""

    async def list_tools(self):
        tools = await super().list_tools()
        exposed_tools = []
        for tool in tools:
            updates = {
                "description": f"{tool.description or ''}{WHITEINTEL_RATE_DISCLOSURE}",
            }
            if tool.name == "card_check":
                input_schema = dict(tool.input_schema)
                input_schema["oneOf"] = [
                    {
                        "title": "Select cards by BIN",
                        "required": ["bin"],
                        "properties": {
                            "bin": {"type": "string"},
                            "issuer": {"type": "null"},
                            "country": {"type": "null"},
                        },
                    },
                    {
                        "title": "Select cards by issuer",
                        "required": ["issuer"],
                        "properties": {
                            "bin": {"type": "null"},
                            "issuer": {"type": "string"},
                            "country": {"type": "null"},
                        },
                    },
                    {
                        "title": "Select cards by country",
                        "required": ["country"],
                        "properties": {
                            "bin": {"type": "null"},
                            "issuer": {"type": "null"},
                            "country": {"type": "string"},
                        },
                    },
                ]
                updates["input_schema"] = input_schema
            exposed_tools.append(tool.model_copy(update=updates))
        return exposed_tools


DomainQuery = Annotated[
    str,
    Field(
        min_length=1,
        description="Target registered domain or subdomain without a scheme or path.",
    ),
]
OptionalDomainQuery = Annotated[
    str | None,
    Field(description="Optional domain used to filter results; omit to use the account-wide view."),
]
SourceFilter = Annotated[
    SourceType,
    Field(description="Exposure source: all, stealer, or combolist."),
]
BreachFilter = Annotated[
    BreachType,
    Field(description="Breach ownership category: all, consumer, or corporate."),
]
FeedMode = Annotated[
    ThreatFeedMode | None,
    Field(description="Set to public_news for news mode; omit for the standard posts feed."),
]
SearchFilter = Annotated[
    str | None,
    Field(description="Optional free-text search phrase; non-empty searches require at least 4 characters."),
]
CategoryFilter = Annotated[
    str | list[str] | None,
    Field(description="Optional threat category or list of at most two categories."),
]
IndustryFilter = Annotated[
    str | list[str] | None,
    Field(description="Optional victim industry or list of at most two industries."),
]
NetworkFilter = Annotated[
    str | list[str] | None,
    Field(description="Optional source-network filter."),
]
TaxonomyMode = Annotated[
    ThreatFeedTaxonomy | None,
    Field(description="Return categories, industries, or networks taxonomy values instead of posts."),
]
StartDate = Annotated[
    str | None,
    Field(description="Inclusive UTC start date in YYYY-MM-DD format; provide end_date with it."),
]
EndDate = Annotated[
    str | None,
    Field(description="Inclusive UTC end date in YYYY-MM-DD format; provide start_date with it."),
]
IndependentStartDate = Annotated[
    str | None,
    Field(description="Optional inclusive UTC start date in YYYY-MM-DD format."),
]
IndependentEndDate = Annotated[
    str | None,
    Field(description="Optional inclusive UTC end date in YYYY-MM-DD format."),
]
UsernameFilter = Annotated[
    str | None,
    Field(description="Optional exact leaked username or email filter."),
]
SubdomainFilter = Annotated[
    str | None,
    Field(description="Optional full subdomain filter for a specific host."),
]
Metric = Annotated[
    OverallMetric,
    Field(description="Aggregate metric to compute for the target domain."),
]
LeakSortKey = Annotated[
    Literal["index_date", "log_date"],
    Field(description="Sort by ingestion time (index_date) or incident time (log_date)."),
]
IPAddressQuery = Annotated[
    str,
    Field(description="Target IPv4 or IPv6 address linked to an infostealer record."),
]
ComputerQuery = Annotated[
    str,
    Field(description="Exact compromised computer hostname to investigate."),
]
UsernameQuery = Annotated[
    str,
    Field(description="Exact username or email address to investigate."),
]
LeakIds = Annotated[
    int | list[int],
    Field(description="One WhiteIntel leak ID or an array containing at most five leak IDs."),
]
WatchlistKind = Annotated[
    WatchlistEntryType | None,
    Field(description="Optional watchlist entry type used to filter the list."),
]
WatchlistState = Annotated[
    WatchlistStatus | None,
    Field(description="Optional enabled or disabled watchlist status filter."),
]
WatchlistEntryKind = Annotated[
    WatchlistEntryType,
    Field(description="Resource type stored in the watchlist."),
]
WatchlistEntry = Annotated[
    str,
    Field(min_length=1, description="Domain, email, hostname, IP, keyword, or repository value to monitor."),
]
NotificationEmail = Annotated[
    str | None,
    Field(description="Optional email address that receives alerts for this entry."),
]
BooleanOption = Annotated[
    bool,
    Field(description="Whether to enable the named notification or data-inclusion option."),
]
RecordId = Annotated[
    int,
    Field(ge=1, description="Positive WhiteIntel record identifier."),
]
OptionalRecordId = Annotated[
    int | None,
    Field(ge=1, description="Optional positive record ID; provide this or domain, but not both."),
]
SupplierState = Annotated[
    SupplierStatus,
    Field(description="Supplier lifecycle state to list: active, paused, archived, or all."),
]
SupplierTierFilter = Annotated[
    SupplierTier | None,
    Field(description="Optional supplier criticality tier filter."),
]
SupplierSearch = Annotated[
    str | None,
    Field(description="Optional free-text supplier name or domain filter."),
]
SupplierSortKey = Annotated[
    SupplierSort,
    Field(description="Supplier list sort key."),
]
SupplierSortOrder = Annotated[
    SortOrder,
    Field(description="Ascending or descending supplier list order."),
]
SupplierDomain = Annotated[
    str,
    Field(min_length=1, description="Supplier registered domain without scheme or path."),
]
OptionalSupplierDomain = Annotated[
    str | None,
    Field(description="Supplier domain selector; provide this or id, but not both."),
]
OptionalLabel = Annotated[
    str | None,
    Field(description="Optional human-readable value for the named supplier attribute."),
]
OptionalNotes = Annotated[
    str | None,
    Field(description="Optional internal notes retained with the supplier record."),
]
SupplierTierValue = Annotated[
    SupplierTier | None,
    Field(description="Optional supplier criticality tier."),
]
OptionalCardIssuer = Annotated[
    str | None,
    Field(
        min_length=3,
        max_length=100,
        description="Optional case-insensitive partial issuing-institution name.",
    ),
]
OptionalCardCountry = Annotated[
    str | None,
    Field(
        min_length=2,
        max_length=100,
        description="Optional ISO alpha-2 country code or partial country name.",
    ),
]
OptionalStringList = Annotated[
    list[str] | None,
    Field(
        min_length=1,
        max_length=10,
        description="Optional list of up to 10 accepted card-attribute values.",
    ),
]
CardTypes = Annotated[
    list[Literal["credit", "debit"]] | None,
    Field(
        min_length=1,
        max_length=10,
        description="Optional card funding types: credit, debit, or both.",
    ),
]
CardCountries = Annotated[
    list[str] | None,
    Field(
        min_length=1,
        max_length=20,
        description="Optional uppercase ISO alpha-2 issuing-country filters.",
    ),
]
CardDate = Annotated[
    str | None,
    Field(description="Optional inclusive exposure-date bound in YYYY-MM-DD format."),
]
CardSortKey = Annotated[
    CardCheckSortBy,
    Field(description="Sort compromised cards by exposed_date or expiry."),
]
CardSortDirection = Annotated[
    CardCheckSortDir,
    Field(description="Ascending or descending compromised-card sort order."),
]
ValidOnly = Annotated[
    bool,
    Field(description="When true, return only cards whose expiry date is still valid."),
]


def _is_loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def _register_doc_resources(mcp: MCPServer) -> None:
    package_docs = Path(__file__).resolve().parent / "docs"
    source_docs = Path(__file__).resolve().parents[2] / "docs"
    docs_dir = package_docs if package_docs.exists() else source_docs
    if not docs_dir.exists():
        return

    for path in sorted(docs_dir.glob("*.md")):

        def make_reader(doc_path: Path):
            def read_doc() -> str:
                return doc_path.read_text(encoding="utf-8")

            return read_doc

        mcp.resource(
            f"whiteintel://docs/{path.name}",
            name=f"docs/{path.stem}",
            description=f"WhiteIntel API documentation: {path.name}",
            mime_type="text/markdown",
        )(make_reader(path))


def create_server(
    enable_write_tools: bool | None = None,
    *,
    auth: AuthSettings | None = None,
    token_verifier: TokenVerifier | None = None,
) -> MCPServer:
    """Build and return the configured MCP server instance."""

    client = WhiteIntelClient(rate_limiter=UpstreamRateLimiter.from_environment())

    if (auth is None) != (token_verifier is None):
        raise ValueError("auth and token_verifier must be provided together.")

    policy = ToolPolicy.from_environment(enable_write_tools=enable_write_tools)

    async def call(endpoint: str, request: BaseModel) -> WhiteIntelResponse:
        body = request.model_dump(exclude_none=True)
        result = await client.call(endpoint, body)
        if not result.get("success", False):
            raise to_tool_error(result)
        return WhiteIntelResponse.model_validate(result)

    @asynccontextmanager
    async def lifespan(server: MCPServer):
        await client.start()
        try:
            yield
        finally:
            await client.aclose()

    mcp = WhiteIntelMCPServer(
        "whiteintel-mcp",
        title="WhiteIntel MCP",
        description="Credential exposure, threat feed, watchlist, and supplier intelligence.",
        instructions=SERVER_INSTRUCTIONS,
        version=__version__,
        lifespan=lifespan,
        auth=auth,
        token_verifier=token_verifier,
    )
    _register_doc_resources(mcp)

    @mcp.tool(
        title="Recent Domain Credential Exposures",
        description=(
            "Get the most recent credential exposures for a target domain within a "
            "1–30 day window. Returns both consumer records (site-level URL match) "
            "and corporate records (email-domain match) in a single call, filtered "
            "by the breach_type parameter. For investigations beyond 30 days, call "
            "consumer_leaks and corporate_leaks separately with date ranges. Use "
            "leaks_by_id after obtaining exact record IDs from any leak tool. This "
            "read-only request consumes the configured account quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def last_leaks(
        query: DomainQuery,
        days: Days = 7,
        data_type: SourceFilter = "all",
        breach_type: BreachFilter = "all",
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        sort_by: LeakSortKey = "index_date",
    ) -> WhiteIntelResponse:
        """Get the most recent credential exposures for a target domain."""
        return await call(
            "last_leaks",
            LastLeaksRequest(
                apikey="",
                query=query,
                days=days,
                data_type=data_type,
                breach_type=breach_type,
                mask_password=mask_password,
                limit=limit,
                page=page,
                sortBy=sort_by,
            ),
        )

    @mcp.tool(
        title="WhiteIntel Threat Feed",
        description=(
            "Query standard WhiteIntel threat-feed posts, public news, or taxonomy "
            "values. Use threat_feed_darkweb_chatters only for the dedicated Darkweb "
            "Chatters add-on. This read-only request requires the Threat Feed "
            "entitlement and consumes its separate quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def threat_feed(
        mode: FeedMode = None,
        search: SearchFilter = None,
        category: CategoryFilter = None,
        industry: IndustryFilter = None,
        network: NetworkFilter = None,
        taxonomy: TaxonomyMode = None,
        start_date: IndependentStartDate = None,
        end_date: IndependentEndDate = None,
        limit: Limit100 = 100,
        page: PositiveInt = 1,
    ) -> WhiteIntelResponse:
        """Query the WhiteIntel threat feed; requires the Threat Feed entitlement."""
        return await call(
            "threat_feed",
            ThreatFeedRequest(
                apikey="",
                mode=mode,
                search=search,
                category=category,
                industry=industry,
                network=network,
                taxonomy=taxonomy,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                page=page,
            ),
        )

    @mcp.tool(
        title="Query Darkweb Chatters Threat Intelligence",
        description=(
            "Query the Darkweb Chatters feed using post, public-news, or taxonomy "
            "filters. Use threat_feed for the standard WhiteIntel feed. This read-only "
            "request requires the dedicated Darkweb Chatters add-on and consumes "
            "Threat Feed quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def threat_feed_darkweb_chatters(
        mode: FeedMode = None,
        search: SearchFilter = None,
        category: CategoryFilter = None,
        industry: IndustryFilter = None,
        network: NetworkFilter = None,
        taxonomy: TaxonomyMode = None,
        start_date: IndependentStartDate = None,
        end_date: IndependentEndDate = None,
        limit: Limit100 = 100,
        page: PositiveInt = 1,
    ) -> WhiteIntelResponse:
        """Query Darkweb Chatters; requires its dedicated Threat Feed add-on."""
        return await call(
            "threat_feed_darkweb_chatters",
            DarkwebChattersRequest(
                apikey="",
                mode=mode,
                search=search,
                category=category,
                industry=industry,
                network=network,
                taxonomy=taxonomy,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                page=page,
            ),
        )

    @mcp.tool(
        title="Consumer Credential Exposures",
        description=(
            "Get credentials stolen from a target domain's own website. Matches the "
            "URL where credentials were captured — returns records from pages under "
            "the queried domain regardless of the victim's email domain, revealing "
            "site-level compromise of the domain itself. Use corporate_leaks "
            "alongside this tool to also find mailboxes belonging to the queried "
            "email domain that were compromised on third-party "
            "sites; the two are complementary and should be called together for full "
            "exposure coverage. Use database_leaks for third-party database "
            "breaches, or last_leaks when recency within 30 days is the primary "
            "filter. This read-only request consumes daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def consumer_leaks(
        query: DomainQuery,
        type: SourceFilter = "all",
        include_system_info: BinaryInt = 0,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: StartDate = None,
        end_date: EndDate = None,
        username: UsernameFilter = None,
        subdomain: SubdomainFilter = None,
    ) -> WhiteIntelResponse:
        """Get consumer-side credentials leaked from infostealers and combolists."""
        return await call(
            "consumer_leaks",
            ConsumerLeaksRequest(
                apikey="",
                query=query,
                type=type,
                include_system_info=include_system_info,
                mask_password=mask_password,
                limit=limit,
                page=page,
                start_date=start_date,
                end_date=end_date,
                username=username,
                subdomain=subdomain,
            ),
        )

    @mcp.tool(
        title="Corporate Credential Exposures",
        description=(
            "Get credentials belonging to an organization's email domain. Matches "
            "the username's email suffix — returns mailboxes belonging to the "
            "queried email domain that were "
            "compromised on any third-party site, regardless of where the "
            "credential was captured. Non-employees may use the same email domain "
            "(especially short or generic domains), producing false "
            "positives; filter results by known employee patterns accordingly. Use "
            "consumer_leaks alongside this tool to also find credentials stolen "
            "from the queried domain's own website; the two are complementary and should "
            "be called together for full exposure coverage. This read-only request "
            "consumes the configured account's daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def corporate_leaks(
        query: DomainQuery,
        type: SourceFilter = "all",
        include_system_info: BinaryInt = 0,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: StartDate = None,
        end_date: EndDate = None,
    ) -> WhiteIntelResponse:
        """Get corporate credentials belonging to an organization."""
        return await call(
            "corporate_leaks",
            CorporateLeaksRequest(
                apikey="",
                query=query,
                type=type,
                include_system_info=include_system_info,
                mask_password=mask_password,
                limit=limit,
                page=page,
                start_date=start_date,
                end_date=end_date,
            ),
        )

    @mcp.tool(
        title="Third-Party Database Breaches",
        description=(
            "Get credentials for a target organization that were exposed specifically "
            "in third-party database breaches. Use corporate_leaks for all supported "
            "corporate exposure sources. This read-only request consumes daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def database_leaks(
        query: DomainQuery,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: StartDate = None,
        end_date: EndDate = None,
    ) -> WhiteIntelResponse:
        """Get corporate credentials exposed in third-party database breaches."""
        return await call(
            "database_leaks",
            DatabaseLeaksRequest(
                apikey="",
                query=query,
                limit=limit,
                page=page,
                start_date=start_date,
                end_date=end_date,
            ),
        )

    @mcp.tool(
        title="Domain Intelligence Metrics",
        description=(
            "Compute one aggregate WhiteIntel exposure metric for a target domain. "
            "Use last_leaks for recent records, or consumer_leaks and corporate_leaks "
            "for source records instead of aggregates. This read-only request returns "
            "one aggregate and consumes daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def overall_stats(query: DomainQuery, metric: Metric) -> WhiteIntelResponse:
        return await call(
            "overall_stats",
            OverallStatsRequest(apikey="", query=query, metric=metric),
        )

    @mcp.tool(
        title="IP-Linked Infostealer Records",
        description=(
            "Get infostealer records linked to an exact IP address. Use "
            "computer_leaks for a hostname or username_leaks for a username or email. "
            "This read-only request requires a Threat Intelligence license and "
            "consumes daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def ip_leaks(
        query: IPAddressQuery,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: StartDate = None,
        end_date: EndDate = None,
    ) -> WhiteIntelResponse:
        """Get IP-linked infostealer records; requires a Threat Intelligence license."""
        return await call(
            "ip_leaks",
            IPLeaksRequest(
                apikey="",
                query=query,
                mask_password=mask_password,
                limit=limit,
                page=page,
                start_date=start_date,
                end_date=end_date,
            ),
        )

    @mcp.tool(
        title="Computer-Linked Credential Exposures",
        description=(
            "Get infostealer credential records for an exact computer hostname. Use "
            "ip_leaks for an IP address or username_leaks for a username or email. "
            "This read-only request consumes the configured account's daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def computer_leaks(
        query: ComputerQuery,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: StartDate = None,
        end_date: EndDate = None,
    ) -> WhiteIntelResponse:
        """Get infostealer credential records for a specific computer hostname."""
        return await call(
            "computer_leaks",
            ComputerLeaksRequest(
                apikey="",
                query=query,
                mask_password=mask_password,
                limit=limit,
                page=page,
                start_date=start_date,
                end_date=end_date,
            ),
        )

    @mcp.tool(
        title="Username Credential Exposures",
        description=(
            "Get credential records for an exact username or email address. Use "
            "computer_leaks for a hostname, ip_leaks for an IP address, or "
            "consumer_leaks for a domain-wide consumer investigation. This read-only "
            "request consumes daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def username_leaks(
        query: UsernameQuery,
        type: SourceFilter = "all",
        include_system_info: BinaryInt = 0,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: StartDate = None,
        end_date: EndDate = None,
    ) -> WhiteIntelResponse:
        """Get credential records for a specific username or email address."""
        return await call(
            "username_leaks",
            UsernameLeaksRequest(
                apikey="",
                query=query,
                type=type,
                include_system_info=include_system_info,
                mask_password=mask_password,
                limit=limit,
                page=page,
                start_date=start_date,
                end_date=end_date,
            ),
        )

    @mcp.tool(
        title="Lookalike and Impersonation Domains",
        description=(
            "List typosquatting and brand-impersonation domains, optionally filtered "
            "by a target domain. Use watchlist_list for domains already under active "
            "monitoring. This read-only request consumes daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def lookalike_domains(
        query: OptionalDomainQuery = None,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
    ) -> WhiteIntelResponse:
        """Get typosquatting and brand-impersonation domains."""
        return await call(
            "lookalike_domains",
            LookalikeDomainsRequest(apikey="", query=query, limit=limit, page=page),
        )

    @mcp.tool(
        title="Leak Records by ID",
        description=(
            "Retrieve full stealer infection records for one known WhiteIntel leak ID "
            "or up to five IDs. When IDs are unknown, use last_leaks, ip_leaks, "
            "computer_leaks, or username_leaks first. This read-only request can reveal "
            "sensitive credential details and consumes daily quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def leaks_by_id(
        query: LeakIds,
        mask_password: BinaryInt = 0,
    ) -> WhiteIntelResponse:
        """Get full stealer infection records by one ID or an array of up to 5 IDs."""
        return await call(
            "leaks_by_id",
            LeaksByIDRequest(apikey="", query=query, mask_password=mask_password),
        )

    @mcp.tool(
        title="List WhiteIntel Watchlist Entries",
        description=(
            "List configured watchlist entries with optional type and status filters. "
            "Use watchlist_add, watchlist_enable, watchlist_disable, or "
            "watchlist_remove only when write tools are explicitly enabled. This "
            "operation is read-only."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def watchlist_list(
        kind: WatchlistKind = None,
        status: WatchlistState = None,
        page: PositiveInt = 1,
        limit: Limit100 = 50,
    ) -> WhiteIntelResponse:
        """List watchlist entries."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(
                apikey="",
                action="list",
                type=kind,
                status=status,
                page=page,
                limit=limit,
            ),
        )

    @mcp.tool(
        title="Add WhiteIntel Watchlist Entry",
        description=(
            "Create a persistent WhiteIntel watchlist entry and its notification "
            "settings. Use watchlist_enable for an existing disabled entry instead. "
            "Creation is a non-idempotent remote write and may cause future email, "
            "Slack, or Jira notifications."
        ),
        annotations=MUTATING_TOOL,
    )
    async def watchlist_add(
        entry_type: WatchlistEntryKind,
        entry: WatchlistEntry,
        notify_email: NotificationEmail = None,
        push_to_slack: BooleanOption = False,
        push_to_jira: BooleanOption = False,
        include_usernames: BooleanOption = False,
        include_passwords: BooleanOption = False,
        consumer_alerts: BooleanOption = False,
        corporate_alerts: BooleanOption = False,
    ) -> WhiteIntelResponse:
        """Add a persistent WhiteIntel watchlist entry and notification settings."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(
                apikey="",
                action="add",
                entry_type=entry_type,
                entry=entry,
                notify_email=notify_email,
                push_to_slack=int(push_to_slack),
                push_to_jira=int(push_to_jira),
                include_usernames=int(include_usernames),
                include_passwords=int(include_passwords),
                consumer_alerts=int(consumer_alerts),
                corporate_alerts=int(corporate_alerts),
            ),
        )

    @mcp.tool(
        title="Remove WhiteIntel Watchlist Entry",
        description=(
            "Permanently remove a WhiteIntel watchlist entry and stop its monitoring "
            "and notifications. Use watchlist_disable to pause an entry without "
            "removing it. This destructive remote action is not reversible."
        ),
        annotations=DESTRUCTIVE_TOOL,
    )
    async def watchlist_remove(id: RecordId) -> WhiteIntelResponse:
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="remove", id=id),
        )

    @mcp.tool(
        title="Enable WhiteIntel Watchlist Entry",
        description=(
            "Enable monitoring and notifications for an existing watchlist entry. "
            "Use watchlist_add when the entry does not exist. Repeating this remote "
            "write leaves the entry enabled."
        ),
        annotations=IDEMPOTENT_MUTATION_TOOL,
    )
    async def watchlist_enable(id: RecordId) -> WhiteIntelResponse:
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="enable", id=id),
        )

    @mcp.tool(
        title="Disable WhiteIntel Watchlist Entry",
        description=(
            "Pause monitoring and notifications for an existing watchlist entry "
            "without deleting it. Use watchlist_remove only for permanent removal. "
            "Repeating this remote write leaves the entry disabled."
        ),
        annotations=IDEMPOTENT_MUTATION_TOOL,
    )
    async def watchlist_disable(id: RecordId) -> WhiteIntelResponse:
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="disable", id=id),
        )

    @mcp.tool(
        title="List Supplier Security Suppliers",
        description=(
            "List suppliers tracked by WhiteIntel Supplier Security with lifecycle, "
            "tier, search, sort, and pagination filters. Use supplier_add, "
            "supplier_remove, or supplier_delete only when write tools are explicitly "
            "enabled. This operation is read-only."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def supplier_list(
        status: SupplierState = "active",
        tier: SupplierTierFilter = None,
        search: SupplierSearch = None,
        sort: SupplierSortKey = "score",
        order: SupplierSortOrder = "desc",
        limit: Limit200 = 50,
        offset: NonNegativeInt = 0,
    ) -> WhiteIntelResponse:
        """List Supplier Security suppliers."""
        return await call(
            "supplier",
            SupplierRequest(
                apikey="",
                action="list",
                status=status,
                tier=tier,
                search=search,
                sort=sort,
                order=order,
                limit=limit,
                offset=offset,
            ),
        )

    @mcp.tool(
        title="Add Supplier Security Supplier",
        description=(
            "Create a persistent supplier record for WhiteIntel Supplier Security "
            "tracking. Use supplier_list to check for an existing supplier first. "
            "Creation is a non-idempotent remote write that can initiate future "
            "supplier monitoring."
        ),
        annotations=MUTATING_TOOL,
    )
    async def supplier_add(
        domain: SupplierDomain,
        display_name: OptionalLabel = None,
        size: OptionalLabel = None,
        country: OptionalLabel = None,
        industry: OptionalLabel = None,
        category: OptionalLabel = None,
        supplier_tier: SupplierTierValue = None,
        notes: OptionalNotes = None,
    ) -> WhiteIntelResponse:
        """Add a persistent supplier to WhiteIntel Supplier Security."""
        return await call(
            "supplier",
            SupplierRequest(
                apikey="",
                action="add",
                domain=domain,
                display_name=display_name,
                size=size,
                country=country,
                industry=industry,
                category=category,
                supplier_tier=supplier_tier,
                notes=notes,
            ),
        )

    @mcp.tool(
        title="Stop Supplier Security Tracking",
        description=(
            "Remove a supplier from active Supplier Security tracking while retaining "
            "its supplier record. Use supplier_delete only when the supplier and "
            "retained data must be permanently deleted. Identify the supplier by "
            "exactly one of id or domain."
        ),
        annotations=DESTRUCTIVE_TOOL,
    )
    async def supplier_remove(
        id: OptionalRecordId = None,
        domain: OptionalSupplierDomain = None,
    ) -> WhiteIntelResponse:
        """Remove a supplier from active WhiteIntel Supplier Security tracking."""
        return await call(
            "supplier",
            SupplierRequest(apikey="", action="remove", id=id, domain=domain),
        )

    @mcp.tool(
        title="Permanently Delete Supplier",
        description=(
            "Permanently delete a Supplier Security supplier and its retained data. "
            "Use supplier_remove to stop active tracking while retaining the record. "
            "Identify the supplier by exactly one of id or domain; this destructive "
            "remote action is not reversible."
        ),
        annotations=DESTRUCTIVE_TOOL,
    )
    async def supplier_delete(
        id: OptionalRecordId = None,
        domain: OptionalSupplierDomain = None,
    ) -> WhiteIntelResponse:
        """Permanently delete a WhiteIntel Supplier Security supplier."""
        return await call(
            "supplier",
            SupplierRequest(apikey="", action="delete", id=id, domain=domain),
        )

    @mcp.tool(
        title="WhiteIntel Audit Logs",
        description=(
            "Get one page of audit events for the configured WhiteIntel API key. Use "
            "last_leaks or the entity lookup tools for exposure records instead. This "
            "operation is read-only and consumes the configured account quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def audit_logs(page: PositiveInt = 1) -> WhiteIntelResponse:
        return await call("audit_logs", AuditLogsRequest(apikey="", page=page))

    @mcp.tool(
        title="Compromised Payment Cards",
        description=(
            "Query compromised payment-card records using issuer, geography, network, "
            "type, brand, validity, date, and sort filters. Use consumer_leaks or "
            "corporate_leaks for non-card credentials. Provide exactly one selector: "
            "bin, issuer, or country. This read-only request requires Payment Fraud "
            "access and consumes its quota."
        ),
        annotations=READ_ONLY_TOOL,
    )
    async def card_check(
        bin: OptionalCardBin = None,
        issuer: OptionalCardIssuer = None,
        country: OptionalCardCountry = None,
        networks: OptionalStringList = None,
        types: CardTypes = None,
        brands: OptionalStringList = None,
        countries: CardCountries = None,
        valid_only: ValidOnly = False,
        exposed_after: CardDate = None,
        exposed_before: CardDate = None,
        sort_by: CardSortKey = "exposed_date",
        sort_dir: CardSortDirection = "desc",
        page: PositiveInt = 1,
    ) -> WhiteIntelResponse:
        """Query compromised card records; requires Payment Fraud access."""
        return await call(
            "card_check",
            CardCheckRequest(
                apikey="",
                bin=bin,
                issuer=issuer,
                country=country,
                networks=networks,
                types=types,
                brands=brands,
                countries=countries,
                valid_only=valid_only,
                exposed_after=exposed_after,
                exposed_before=exposed_before,
                sort_by=sort_by,
                sort_dir=sort_dir,
                page=page,
            ),
        )

    policy.apply(mcp)
    return mcp


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(prog="whiteintel-mcp")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=os.getenv("WHITEINTEL_MCP_TRANSPORT", "stdio"),
        help="MCP transport to serve.",
    )
    parser.add_argument("--host", default=os.getenv("WHITEINTEL_MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("WHITEINTEL_MCP_PORT", "8000")))
    parser.add_argument("--streamable-http-path", default=os.getenv("WHITEINTEL_MCP_HTTP_PATH", "/mcp"))
    parser.add_argument("--sse-path", default=os.getenv("WHITEINTEL_MCP_SSE_PATH", "/sse"))
    args = parser.parse_args()

    if (
        args.transport != "stdio"
        and not _is_loopback_host(args.host)
        and not env_flag("WHITEINTEL_MCP_ALLOW_INSECURE_REMOTE")
    ):
        parser.error(
            "Remote HTTP/SSE binding requires MCP OAuth or a trusted authenticating proxy. "
            "Set WHITEINTEL_MCP_ALLOW_INSECURE_REMOTE=true only when that protection is external."
        )

    server = create_server()
    if args.transport == "stdio":
        server.run(transport="stdio")
    elif args.transport == "sse":
        server.run(
            transport="sse",
            host=args.host,
            port=args.port,
            sse_path=args.sse_path,
        )
    else:
        server.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            streamable_http_path=args.streamable_http_path,
        )


if __name__ == "__main__":
    main()
