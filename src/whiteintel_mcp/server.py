"""Aggregate MCP server for WhiteIntel threat intelligence APIs.

Registers one MCP tool per WhiteIntel API endpoint and manages the
httpx client + rate limiter lifecycle.
"""

from __future__ import annotations

import os
import argparse
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from whiteintel_mcp import __version__
from whiteintel_mcp.services.upstream_rate_limiter import UpstreamRateLimiter
from whiteintel_mcp.services.whiteintel_client import WhiteIntelClient
from whiteintel_mcp.tools import api_tools

SERVER_INSTRUCTIONS = (
    "This server exposes WhiteIntel threat intelligence tools for credential exposure, "
    "threat feeds, database leaks, lookalike domains, watchlist management, supplier "
    "security, and audit logs. Use the tool that matches the target WhiteIntel API "
    "data source and prefer WHITEINTEL_API_KEY from the server environment."
)


def apply_server_metadata(server: FastMCP) -> None:
    """Keep FastMCP handshake metadata aligned with package metadata."""
    mcp_server = getattr(server, "_mcp_server", None)
    if mcp_server is not None:
        mcp_server.version = __version__


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    streamable_http_path: str = "/mcp",
    sse_path: str = "/sse",
) -> FastMCP:
    """Build and return the configured FastMCP server instance."""

    # Shared services that outlive a single request.
    rate_limiter = UpstreamRateLimiter()
    client = WhiteIntelClient(rate_limiter=rate_limiter)

    @asynccontextmanager
    async def lifespan(server: FastMCP):
        """Start / stop the HTTP connection pool."""
        await client.start()
        api_tools.set_client(client)
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

    # ------------------------------------------------------------------
    # Tool registration — one tool per WhiteIntel endpoint
    # ------------------------------------------------------------------

    @mcp.tool()
    async def last_leaks(
        query: str,
        apikey: str = "",
        days: int = 7,
        data_type: str = "all",
        breach_type: str = "all",
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
    ) -> dict[str, Any]:
        """Get the most recent credential exposures for a target domain.

        Returns consumer and corporate leak records within a configurable
        look-back window (1–30 days). Supports filtering by source type
        (stealer/combolist) and breach category.
        """
        return await api_tools.last_leaks(
            apikey=apikey,
            query=query,
            days=days,
            data_type=data_type,
            breach_type=breach_type,
            mask_password=mask_password,
            limit=limit,
            page=page,
        )

    @mcp.tool()
    async def threat_feed(
        apikey: str = "",
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
        """Query the WhiteIntel threat intelligence feed.

        Three modes: posts (curated dark-web intelligence with victim/actor metadata),
        public_news (public-source articles), and taxonomy (available filter values).
        """
        return await api_tools.threat_feed(
            apikey=apikey,
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
        )

    @mcp.tool()
    async def consumer_leaks(
        query: str,
        apikey: str = "",
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
        """Get consumer-side credentials leaked from infostealers and combolists.

        Matches against the website where the credential was captured.
        Supports date range, username, and subdomain filters.
        """
        return await api_tools.consumer_leaks(
            apikey=apikey,
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
        )

    @mcp.tool()
    async def corporate_leaks(
        query: str,
        apikey: str = "",
        type: str = "all",
        include_system_info: int = 0,
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get corporate credentials belonging to an organization.

        Matches against the email domain of the leaked username across any
        third-party service where credentials were captured.
        """
        return await api_tools.corporate_leaks(
            apikey=apikey,
            query=query,
            type=type,
            include_system_info=include_system_info,
            mask_password=mask_password,
            limit=limit,
            page=page,
            start_date=start_date,
            end_date=end_date,
        )

    @mcp.tool()
    async def database_leaks(
        query: str,
        apikey: str = "",
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get corporate credentials exposed in third-party database breaches.

        Results are grouped by breach source with breach-level metadata
        (date, description, exposed data fields). Matches by email domain.
        """
        return await api_tools.database_leaks(
            apikey=apikey,
            query=query,
            limit=limit,
            page=page,
            start_date=start_date,
            end_date=end_date,
        )

    @mcp.tool()
    async def overall_stats(
        query: str,
        metric: str,
        apikey: str = "",
    ) -> dict[str, Any]:
        """Get aggregate intelligence metrics for a target domain.

        Supports 13 metrics: consumer_count, corporate_count, computer_count,
        ip_address_count, application_count, third_party_application_count,
        applications, third_party_applications, consumer_incident_timeline,
        corporate_incident_timeline, latest_consumer_events,
        latest_corporate_events, country_stats.
        """
        return await api_tools.overall_stats(
            apikey=apikey,
            query=query,
            metric=metric,
        )

    @mcp.tool()
    async def ip_leaks(
        query: str,
        apikey: str = "",
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get infostealer credential records for a specific IP address.

        Returns stealer logs only (no combolist data). Always includes
        host-level system information when available.
        """
        return await api_tools.ip_leaks(
            apikey=apikey,
            query=query,
            mask_password=mask_password,
            limit=limit,
            page=page,
            start_date=start_date,
            end_date=end_date,
        )

    @mcp.tool()
    async def computer_leaks(
        query: str,
        apikey: str = "",
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get infostealer credential records for a specific computer hostname.

        Uses exact case-sensitive hostname matching. Returns stealer logs only.
        """
        return await api_tools.computer_leaks(
            apikey=apikey,
            query=query,
            mask_password=mask_password,
            limit=limit,
            page=page,
            start_date=start_date,
            end_date=end_date,
        )

    @mcp.tool()
    async def username_leaks(
        query: str,
        apikey: str = "",
        type: str = "all",
        include_system_info: int = 0,
        mask_password: int = 0,
        limit: int = 500,
        page: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get credential records for a specific username or email address.

        Uses exact match on the username field. Has a dedicated username
        search quota separate from the daily API quota.
        """
        return await api_tools.username_leaks(
            apikey=apikey,
            query=query,
            type=type,
            include_system_info=include_system_info,
            mask_password=mask_password,
            limit=limit,
            page=page,
            start_date=start_date,
            end_date=end_date,
        )

    @mcp.tool()
    async def lookalike_domains(
        apikey: str = "",
        query: str | None = None,
        limit: int = 500,
        page: int = 1,
    ) -> dict[str, Any]:
        """Get typosquatting and brand-impersonation domains.

        Omit query for organization-wide mode (all watchlist entries).
        Supply a watchlist domain to scope results to that entry.
        """
        return await api_tools.lookalike_domains(
            apikey=apikey,
            query=query,
            limit=limit,
            page=page,
        )

    @mcp.tool()
    async def leaks_by_id(
        query: str,
        apikey: str = "",
        mask_password: int = 0,
    ) -> dict[str, Any]:
        """Get full stealer infection records by log ID(s).

        Pass a single ID or a comma-separated list of up to 5 IDs.
        Batched requests consume only 1 daily quota credit.
        """
        # Parse query: single int or comma-separated list.
        if "," in query:
            parsed: int | list[int] = [int(x.strip()) for x in query.split(",") if x.strip()]
        else:
            parsed = int(query)
        return await api_tools.leaks_by_id(
            apikey=apikey,
            query=parsed,
            mask_password=mask_password,
        )

    @mcp.tool()
    async def watchlist_manage(
        action: str,
        apikey: str = "",
        entry_type: str | None = None,
        entry: str | None = None,
        id: int | None = None,
        type: str | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 50,
        notify_email: str | None = None,
        push_to_slack: int = 0,
        push_to_jira: int = 0,
        include_usernames: int = 0,
        include_passwords: int = 0,
        consumer_alerts: int = 0,
        corporate_alerts: int = 0,
    ) -> dict[str, Any]:
        """Manage watchlist entries: list, add, remove, enable, or disable.

        Credits: adding consumes 1 credit, removing refunds 1 credit.
        Enabling/disabling does not change credits.
        """
        return await api_tools.watchlist_manage(
            apikey=apikey,
            action=action,
            entry_type=entry_type,
            entry=entry,
            id=id,
            type=type,
            status=status,
            page=page,
            limit=limit,
            notify_email=notify_email,
            push_to_slack=push_to_slack,
            push_to_jira=push_to_jira,
            include_usernames=include_usernames,
            include_passwords=include_passwords,
            consumer_alerts=consumer_alerts,
            corporate_alerts=corporate_alerts,
        )

    @mcp.tool()
    async def supplier(
        action: str,
        apikey: str = "",
        status: str = "active",
        tier: str | None = None,
        search: str | None = None,
        sort: str = "score",
        order: str = "desc",
        limit: int = 50,
        offset: int = 0,
        domain: str | None = None,
        id: int | None = None,
        display_name: str | None = None,
        size: str | None = None,
        country: str | None = None,
        industry: str | None = None,
        category: str | None = None,
        supplier_tier: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Manage Supplier Security suppliers: list, add, remove, or delete.

        Listing supports status/tier/search/sort/order/limit/offset.
        Adding requires domain. Removing accepts id or domain; id takes precedence upstream.
        """
        return await api_tools.supplier(
            apikey=apikey,
            action=action,
            status=status,
            tier=tier,
            search=search,
            sort=sort,
            order=order,
            limit=limit,
            offset=offset,
            domain=domain,
            id=id,
            display_name=display_name,
            size=size,
            country=country,
            industry=industry,
            category=category,
            supplier_tier=supplier_tier,
            notes=notes,
        )

    @mcp.tool()
    async def audit_logs(
        apikey: str = "",
        page: int = 1,
    ) -> dict[str, Any]:
        """Get paginated audit logs for an API key.

        Returns IP, timestamp, HTTP method, and query type for each call.
        """
        return await api_tools.audit_logs(
            apikey=apikey,
            page=page,
        )

    return mcp


def main() -> None:
    """Entry point: create and run the MCP server."""
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
