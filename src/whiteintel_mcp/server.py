"""FastMCP server for WhiteIntel threat intelligence APIs."""

from __future__ import annotations

import argparse
import os
from contextlib import asynccontextmanager
from ipaddress import ip_address
from pathlib import Path
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
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
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)
MUTATING_TOOL = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)
IDEMPOTENT_MUTATION_TOOL = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)
DESTRUCTIVE_TOOL = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=True,
)

PositiveInt = Annotated[int, Field(ge=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]
BinaryInt = Annotated[int, Field(ge=0, le=1)]
Days = Annotated[int, Field(ge=1, le=30)]
Limit100 = Annotated[int, Field(ge=1, le=100)]
Limit200 = Annotated[int, Field(ge=1, le=200)]
Limit5000 = Annotated[int, Field(ge=1, le=5000)]
CardBin = Annotated[str, Field(min_length=6, max_length=8, pattern=r"^\d{6,8}$")]
CountryCode = Annotated[str, Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")]


def _is_loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def apply_server_metadata(server: FastMCP) -> None:
    """Keep FastMCP handshake metadata aligned with package metadata."""
    mcp_server = getattr(server, "_mcp_server", None)
    if mcp_server is not None:
        mcp_server.version = __version__


def _register_doc_resources(mcp: FastMCP) -> None:
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
    host: str = "127.0.0.1",
    port: int = 8000,
    streamable_http_path: str = "/mcp",
    sse_path: str = "/sse",
    *,
    enable_write_tools: bool | None = None,
    auth: AuthSettings | None = None,
    token_verifier: TokenVerifier | None = None,
) -> FastMCP:
    """Build and return the configured FastMCP server instance."""

    client = WhiteIntelClient(rate_limiter=UpstreamRateLimiter())

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
    async def lifespan(server: FastMCP):
        await client.start()
        try:
            yield
        finally:
            await client.aclose()

    mcp = FastMCP(
        "whiteintel-mcp",
        instructions=SERVER_INSTRUCTIONS,
        host=host,
        port=port,
        streamable_http_path=streamable_http_path,
        sse_path=sse_path,
        lifespan=lifespan,
        auth=auth,
        token_verifier=token_verifier,
    )
    apply_server_metadata(mcp)
    _register_doc_resources(mcp)

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def last_leaks(
        query: str,
        days: Days = 7,
        data_type: SourceType = "all",
        breach_type: BreachType = "all",
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        sort_by: Literal["index_date", "log_date"] = "index_date",
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def threat_feed(
        mode: ThreatFeedMode | None = None,
        search: str | None = None,
        category: str | list[str] | None = None,
        industry: str | list[str] | None = None,
        network: str | list[str] | None = None,
        taxonomy: ThreatFeedTaxonomy | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def threat_feed_darkweb_chatters(
        mode: ThreatFeedMode | None = None,
        search: str | None = None,
        category: str | list[str] | None = None,
        industry: str | list[str] | None = None,
        network: str | list[str] | None = None,
        taxonomy: ThreatFeedTaxonomy | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def consumer_leaks(
        query: str,
        type: SourceType = "all",
        include_system_info: BinaryInt = 0,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: str | None = None,
        end_date: str | None = None,
        username: str | None = None,
        subdomain: str | None = None,
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def corporate_leaks(
        query: str,
        type: SourceType = "all",
        include_system_info: BinaryInt = 0,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: str | None = None,
        end_date: str | None = None,
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def database_leaks(
        query: str,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: str | None = None,
        end_date: str | None = None,
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def overall_stats(query: str, metric: OverallMetric) -> WhiteIntelResponse:
        """Get aggregate intelligence metrics for a target domain."""
        return await call(
            "overall_stats",
            OverallStatsRequest(apikey="", query=query, metric=metric),
        )

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def ip_leaks(
        query: str,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: str | None = None,
        end_date: str | None = None,
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def computer_leaks(
        query: str,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: str | None = None,
        end_date: str | None = None,
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def username_leaks(
        query: str,
        type: SourceType = "all",
        include_system_info: BinaryInt = 0,
        mask_password: BinaryInt = 0,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
        start_date: str | None = None,
        end_date: str | None = None,
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

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def lookalike_domains(
        query: str | None = None,
        limit: Limit5000 = 500,
        page: PositiveInt = 1,
    ) -> WhiteIntelResponse:
        """Get typosquatting and brand-impersonation domains."""
        return await call(
            "lookalike_domains",
            LookalikeDomainsRequest(apikey="", query=query, limit=limit, page=page),
        )

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def leaks_by_id(
        query: int | list[int],
        mask_password: BinaryInt = 0,
    ) -> WhiteIntelResponse:
        """Get full stealer infection records by one ID or an array of up to 5 IDs."""
        return await call(
            "leaks_by_id",
            LeaksByIDRequest(apikey="", query=query, mask_password=mask_password),
        )

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def watchlist_list(
        kind: WatchlistEntryType | None = None,
        status: WatchlistStatus | None = None,
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

    @mcp.tool(annotations=MUTATING_TOOL)
    async def watchlist_add(
        entry_type: WatchlistEntryType,
        entry: str,
        notify_email: str | None = None,
        push_to_slack: bool = False,
        push_to_jira: bool = False,
        include_usernames: bool = False,
        include_passwords: bool = False,
        consumer_alerts: bool = False,
        corporate_alerts: bool = False,
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

    @mcp.tool(annotations=DESTRUCTIVE_TOOL)
    async def watchlist_remove(id: PositiveInt) -> WhiteIntelResponse:
        """Permanently remove a WhiteIntel watchlist entry."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="remove", id=id),
        )

    @mcp.tool(annotations=IDEMPOTENT_MUTATION_TOOL)
    async def watchlist_enable(id: PositiveInt) -> WhiteIntelResponse:
        """Enable a watchlist entry."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="enable", id=id),
        )

    @mcp.tool(annotations=IDEMPOTENT_MUTATION_TOOL)
    async def watchlist_disable(id: PositiveInt) -> WhiteIntelResponse:
        """Disable a watchlist entry."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="disable", id=id),
        )

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def supplier_list(
        status: SupplierStatus = "active",
        tier: SupplierTier | None = None,
        search: str | None = None,
        sort: SupplierSort = "score",
        order: SortOrder = "desc",
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

    @mcp.tool(annotations=MUTATING_TOOL)
    async def supplier_add(
        domain: str,
        display_name: str | None = None,
        size: str | None = None,
        country: str | None = None,
        industry: str | None = None,
        category: str | None = None,
        supplier_tier: SupplierTier | None = None,
        notes: str | None = None,
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

    @mcp.tool(annotations=DESTRUCTIVE_TOOL)
    async def supplier_remove(
        id: PositiveInt | None = None,
        domain: str | None = None,
    ) -> WhiteIntelResponse:
        """Remove a supplier from active WhiteIntel Supplier Security tracking."""
        return await call(
            "supplier",
            SupplierRequest(apikey="", action="remove", id=id, domain=domain),
        )

    @mcp.tool(annotations=DESTRUCTIVE_TOOL)
    async def supplier_delete(
        id: PositiveInt | None = None,
        domain: str | None = None,
    ) -> WhiteIntelResponse:
        """Permanently delete a WhiteIntel Supplier Security supplier."""
        return await call(
            "supplier",
            SupplierRequest(apikey="", action="delete", id=id, domain=domain),
        )

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def audit_logs(page: PositiveInt = 1) -> WhiteIntelResponse:
        """Get paginated audit logs for the configured API key."""
        return await call("audit_logs", AuditLogsRequest(apikey="", page=page))

    @mcp.tool(annotations=READ_ONLY_TOOL)
    async def card_check(
        bin: CardBin | None = None,
        issuer: str | None = None,
        country: CountryCode | None = None,
        networks: list[str] | None = None,
        types: list[Literal["credit", "debit"]] | None = None,
        brands: list[str] | None = None,
        valid_only: bool = False,
        exposed_after: str | None = None,
        exposed_before: str | None = None,
        sort_by: CardCheckSortBy = "exposed_date",
        sort_dir: CardCheckSortDir = "desc",
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
                valid_only=int(valid_only),
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
    parser.add_argument("--mount-path", default=os.getenv("WHITEINTEL_MCP_MOUNT_PATH", None))
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

    create_server(
        host=args.host,
        port=args.port,
        streamable_http_path=args.streamable_http_path,
        sse_path=args.sse_path,
    ).run(transport=args.transport, mount_path=args.mount_path)


if __name__ == "__main__":
    main()
