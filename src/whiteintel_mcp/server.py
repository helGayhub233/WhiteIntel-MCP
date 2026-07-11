"""FastMCP server for WhiteIntel threat intelligence APIs."""

from __future__ import annotations

import argparse
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from whiteintel_mcp import __version__
from whiteintel_mcp.models.endpoints import (
    AuditLogsRequest,
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
    SupplierRequest,
    ThreatFeedRequest,
    UsernameLeaksRequest,
    WatchlistManageRequest,
)
from whiteintel_mcp.services.upstream_rate_limiter import UpstreamRateLimiter
from whiteintel_mcp.services.whiteintel_client import WhiteIntelClient


SERVER_INSTRUCTIONS = (
    "This server exposes WhiteIntel threat intelligence tools for credential exposure, "
    "threat feeds, database leaks, lookalike domains, watchlist management, supplier "
    "security, card check, and audit logs. The API key is read from the "
    "WHITEINTEL_API_KEY server environment variable."
)


def apply_server_metadata(server: FastMCP) -> None:
    """Keep FastMCP handshake metadata aligned with package metadata."""
    mcp_server = getattr(server, "_mcp_server", None)
    if mcp_server is not None:
        mcp_server.version = __version__


def _csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


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
) -> FastMCP:
    """Build and return the configured FastMCP server instance."""

    client = WhiteIntelClient(rate_limiter=UpstreamRateLimiter())

    async def call(endpoint: str, request: BaseModel) -> dict[str, Any]:
        body = request.model_dump(exclude_none=True)
        return await client.call(endpoint, body)

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
    )
    apply_server_metadata(mcp)
    _register_doc_resources(mcp)

    @mcp.tool()
    async def last_leaks(
        query: str,
        days: int = 7,
        data_type: str = "all",
        breach_type: str = "all",
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        sortBy: str = "index_date",
    ) -> dict[str, Any]:
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
                sortBy=sortBy,
            ),
        )

    @mcp.tool()
    async def threat_feed(
        mode: str | None = None,
        search: str | None = None,
        category: str | list[str] | None = None,
        industry: str | list[str] | None = None,
        network: str | list[str] | None = None,
        taxonomy: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict[str, Any]:
        """Query the WhiteIntel threat intelligence feed."""
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

    @mcp.tool()
    async def threat_feed_darkweb_chatters(
        mode: str | None = None,
        search: str | None = None,
        category: str | list[str] | None = None,
        industry: str | list[str] | None = None,
        network: str | list[str] | None = None,
        taxonomy: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict[str, Any]:
        """Query the Threat Feed Darkweb Chatters add-on."""
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

    @mcp.tool()
    async def consumer_leaks(
        query: str,
        type: str = "all",
        include_system_info: int = 0,
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
        username: str | None = None,
        subdomain: str | None = None,
    ) -> dict[str, Any]:
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

    @mcp.tool()
    async def corporate_leaks(
        query: str,
        type: str = "all",
        include_system_info: int = 0,
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
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

    @mcp.tool()
    async def database_leaks(
        query: str,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
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

    @mcp.tool()
    async def overall_stats(query: str, metric: str) -> dict[str, Any]:
        """Get aggregate intelligence metrics for a target domain."""
        return await call(
            "overall_stats",
            OverallStatsRequest(apikey="", query=query, metric=metric),
        )

    @mcp.tool()
    async def ip_leaks(
        query: str,
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get infostealer credential records for a specific IP address."""
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

    @mcp.tool()
    async def computer_leaks(
        query: str,
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
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

    @mcp.tool()
    async def username_leaks(
        query: str,
        type: str = "all",
        include_system_info: int = 0,
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
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

    @mcp.tool()
    async def lookalike_domains(
        query: str | None = None,
        limit: int = 500,
        page: int = 1,
    ) -> dict[str, Any]:
        """Get typosquatting and brand-impersonation domains."""
        return await call(
            "lookalike_domains",
            LookalikeDomainsRequest(apikey="", query=query, limit=limit, page=page),
        )

    @mcp.tool()
    async def leaks_by_id(query: str, mask_password: int = 0) -> dict[str, Any]:
        """Get full stealer infection records by log ID or up to 5 comma-separated IDs."""
        parsed: int | list[int]
        if "," in query:
            parsed = [int(item.strip()) for item in query.split(",") if item.strip()]
        else:
            parsed = int(query)
        return await call(
            "leaks_by_id",
            LeaksByIDRequest(apikey="", query=parsed, mask_password=mask_password),
        )

    @mcp.tool()
    async def watchlist_list(
        kind: str | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
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

    @mcp.tool()
    async def watchlist_add(
        entry_type: str,
        entry: str,
        notify_email: str | None = None,
        push_to_slack: int = 0,
        push_to_jira: int = 0,
        include_usernames: int = 0,
        include_passwords: int = 0,
        consumer_alerts: int = 0,
        corporate_alerts: int = 0,
    ) -> dict[str, Any]:
        """Add a watchlist entry."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(
                apikey="",
                action="add",
                entry_type=entry_type,
                entry=entry,
                notify_email=notify_email,
                push_to_slack=push_to_slack,
                push_to_jira=push_to_jira,
                include_usernames=include_usernames,
                include_passwords=include_passwords,
                consumer_alerts=consumer_alerts,
                corporate_alerts=corporate_alerts,
            ),
        )

    @mcp.tool()
    async def watchlist_remove(id: int) -> dict[str, Any]:
        """Remove a watchlist entry."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="remove", id=id),
        )

    @mcp.tool()
    async def watchlist_enable(id: int) -> dict[str, Any]:
        """Enable a watchlist entry."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="enable", id=id),
        )

    @mcp.tool()
    async def watchlist_disable(id: int) -> dict[str, Any]:
        """Disable a watchlist entry."""
        return await call(
            "watchlist_manage",
            WatchlistManageRequest(apikey="", action="disable", id=id),
        )

    @mcp.tool()
    async def supplier_list(
        status: str = "active",
        tier: str | None = None,
        search: str | None = None,
        sort: str = "score",
        order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
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

    @mcp.tool()
    async def supplier_add(
        domain: str,
        display_name: str | None = None,
        size: str | None = None,
        country: str | None = None,
        industry: str | None = None,
        category: str | None = None,
        supplier_tier: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Add a Supplier Security supplier."""
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

    @mcp.tool()
    async def supplier_remove(id: int | None = None, domain: str | None = None) -> dict[str, Any]:
        """Remove a Supplier Security supplier."""
        return await call(
            "supplier",
            SupplierRequest(apikey="", action="remove", id=id, domain=domain),
        )

    @mcp.tool()
    async def supplier_delete(id: int | None = None, domain: str | None = None) -> dict[str, Any]:
        """Delete a Supplier Security supplier."""
        return await call(
            "supplier",
            SupplierRequest(apikey="", action="delete", id=id, domain=domain),
        )

    @mcp.tool()
    async def audit_logs(page: int = 1) -> dict[str, Any]:
        """Get paginated audit logs for the configured API key."""
        return await call("audit_logs", AuditLogsRequest(apikey="", page=page))

    @mcp.tool()
    async def card_check(
        bin: str | None = None,
        issuer: str | None = None,
        country: str | None = None,
        networks: str | None = None,
        types: str | None = None,
        brands: str | None = None,
        valid_only: int = 0,
        exposed_after: str | None = None,
        exposed_before: str | None = None,
        sort_by: str = "exposed_date",
        sort_dir: str = "desc",
        page: int = 1,
    ) -> dict[str, Any]:
        """Query compromised payment card records."""
        return await call(
            "card_check",
            CardCheckRequest(
                apikey="",
                bin=bin,
                issuer=issuer,
                country=country,
                networks=_csv(networks),
                types=_csv(types),
                brands=_csv(brands),
                valid_only=valid_only,
                exposed_after=exposed_after,
                exposed_before=exposed_before,
                sort_by=sort_by,
                sort_dir=sort_dir,
                page=page,
            ),
        )

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

    create_server(
        host=args.host,
        port=args.port,
        streamable_http_path=args.streamable_http_path,
        sse_path=args.sse_path,
    ).run(transport=args.transport, mount_path=args.mount_path)


if __name__ == "__main__":
    main()
