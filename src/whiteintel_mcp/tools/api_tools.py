"""MCP tool implementations for every WhiteIntel API endpoint.

Each function accepts the full parameter set of the corresponding endpoint,
constructs a Pydantic model, and delegates to WhiteIntelClient.call().

The module-level ``_client`` reference is set by the server lifespan so that
tools do not need to carry it as a parameter.
"""

from __future__ import annotations

import os
from typing import Any

from whiteintel_mcp.models.endpoints import (
    AuditLogsRequest,
    ComputerLeaksRequest,
    ConsumerLeaksRequest,
    CorporateLeaksRequest,
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
from whiteintel_mcp.services.whiteintel_client import WhiteIntelClient

# Set during server lifespan by create_server().
_client: WhiteIntelClient | None = None


def set_client(client: WhiteIntelClient) -> None:
    """Inject the shared HTTP client (called once during server startup)."""
    global _client
    _client = client


def _get_client() -> WhiteIntelClient:
    if _client is None:
        raise RuntimeError("WhiteIntel client not initialised – server lifespan may have failed.")
    return _client


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _call(endpoint: str, model: Any) -> dict[str, Any]:
    """Dump the Pydantic model to dict and forward to the upstream client."""
    body = model.model_dump(exclude_none=True)
    body.setdefault("apikey", os.getenv("WHITEINTEL_API_KEY", ""))
    return _get_client().call(endpoint, body)


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

# --- Last Leaks ---

async def last_leaks(
    apikey: str,
    query: str,
    days: int = 7,
    data_type: str = "all",
    breach_type: str = "all",
    mask_password: int = 0,
    limit: int = 1000,
    page: int = 1,
) -> dict[str, Any]:
    """Get the most recent credential exposures for a target domain."""
    model = LastLeaksRequest(
        apikey=apikey,
        query=query,
        days=days,
        data_type=data_type,
        breach_type=breach_type,
        mask_password=mask_password,
        limit=limit,
        page=page,
    )
    return await _call("last_leaks", model)


# --- Threat Feed ---

async def threat_feed(
    apikey: str,
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
    """Query the WhiteIntel threat intelligence feed (posts, public news, or taxonomy)."""
    model = ThreatFeedRequest(
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
    return await _call("threat_feed", model)


# --- Consumer Leaks ---

async def consumer_leaks(
    apikey: str,
    query: str,
    type: str = "all",
    include_system_info: int = 0,
    mask_password: int = 0,
    limit: int = 1000,
    page: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
    username: str | None = None,
    subdomain: str | None = None,
) -> dict[str, Any]:
    """Get consumer-side credential exposures for a domain."""
    model = ConsumerLeaksRequest(
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
    return await _call("consumer_leaks", model)


# --- Corporate Leaks ---

async def corporate_leaks(
    apikey: str,
    query: str,
    type: str = "all",
    include_system_info: int = 0,
    mask_password: int = 0,
    limit: int = 1000,
    page: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get corporate-side credential exposures for an organization."""
    model = CorporateLeaksRequest(
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
    return await _call("corporate_leaks", model)


# --- Database Leaks ---

async def database_leaks(
    apikey: str,
    query: str,
    limit: int = 1000,
    page: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get corporate credentials exposed in third-party database breaches."""
    model = DatabaseLeaksRequest(
        apikey=apikey,
        query=query,
        limit=limit,
        page=page,
        start_date=start_date,
        end_date=end_date,
    )
    return await _call("database_leaks", model)


# --- Overall Stats ---

async def overall_stats(
    apikey: str,
    query: str,
    metric: str,
) -> dict[str, Any]:
    """Get aggregate intelligence metrics for a target domain."""
    model = OverallStatsRequest(
        apikey=apikey,
        query=query,
        metric=metric,
    )
    return await _call("overall_stats", model)


# --- IP Leaks ---

async def ip_leaks(
    apikey: str,
    query: str,
    mask_password: int = 0,
    limit: int = 1000,
    page: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get infostealer credential records for a specific IP address."""
    model = IPLeaksRequest(
        apikey=apikey,
        query=query,
        mask_password=mask_password,
        limit=limit,
        page=page,
        start_date=start_date,
        end_date=end_date,
    )
    return await _call("ip_leaks", model)


# --- Computer Leaks ---

async def computer_leaks(
    apikey: str,
    query: str,
    mask_password: int = 0,
    limit: int = 1000,
    page: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get infostealer credential records for a specific hostname."""
    model = ComputerLeaksRequest(
        apikey=apikey,
        query=query,
        mask_password=mask_password,
        limit=limit,
        page=page,
        start_date=start_date,
        end_date=end_date,
    )
    return await _call("computer_leaks", model)


# --- Username Leaks ---

async def username_leaks(
    apikey: str,
    query: str,
    type: str = "all",
    include_system_info: int = 0,
    mask_password: int = 0,
    limit: int = 1000,
    page: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get credential records for a specific username or email address."""
    model = UsernameLeaksRequest(
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
    return await _call("username_leaks", model)


# --- Lookalike Domains ---

async def lookalike_domains(
    apikey: str,
    query: str | None = None,
    limit: int = 1000,
    page: int = 1,
) -> dict[str, Any]:
    """Get typosquatting and brand-impersonation domains from the watchlist."""
    model = LookalikeDomainsRequest(
        apikey=apikey,
        query=query,
        limit=limit,
        page=page,
    )
    return await _call("lookalike_domains", model)


# --- Get Leaks By ID ---

async def leaks_by_id(
    apikey: str,
    query: int | list[int],
    mask_password: int = 0,
) -> dict[str, Any]:
    """Get full stealer infection records by log ID (single or batch of 1–5)."""
    model = LeaksByIDRequest(
        apikey=apikey,
        query=query,
        mask_password=mask_password,
    )
    return await _call("leaks_by_id", model)


# --- Watchlist Manage ---

async def watchlist_manage(
    apikey: str,
    action: str,
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
    """Manage watchlist entries: list, add, remove, enable, or disable."""
    model = WatchlistManageRequest(
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
    return await _call("watchlist_manage", model)


# --- Supplier Security ---

async def supplier(
    apikey: str,
    action: str,
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
    """Manage Supplier Security tracked suppliers."""
    model = SupplierRequest(
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
    return await _call("supplier", model)


# --- Audit Logs ---

async def audit_logs(
    apikey: str,
    page: int = 1,
) -> dict[str, Any]:
    """Get paginated audit logs for an API key."""
    model = AuditLogsRequest(
        apikey=apikey,
        page=page,
    )
    return await _call("audit_logs", model)
