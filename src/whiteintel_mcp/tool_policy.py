"""Static, fail-closed exposure policy for MCP tools."""

from __future__ import annotations

import os
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP


TOOL_MODULES: dict[str, str] = {
    "last_leaks": "credential_exposure",
    "consumer_leaks": "credential_exposure",
    "corporate_leaks": "credential_exposure",
    "database_leaks": "credential_exposure",
    "threat_feed": "threat_feed",
    "threat_feed_darkweb_chatters": "threat_feed",
    "overall_stats": "analytics",
    "ip_leaks": "entity_lookup",
    "computer_leaks": "entity_lookup",
    "username_leaks": "entity_lookup",
    "leaks_by_id": "entity_lookup",
    "lookalike_domains": "brand_protection",
    "watchlist_list": "watchlist",
    "watchlist_add": "watchlist",
    "watchlist_remove": "watchlist",
    "watchlist_enable": "watchlist",
    "watchlist_disable": "watchlist",
    "supplier_list": "supplier_security",
    "supplier_add": "supplier_security",
    "supplier_remove": "supplier_security",
    "supplier_delete": "supplier_security",
    "audit_logs": "audit",
    "card_check": "payment_fraud",
}

ALL_MODULES = frozenset(TOOL_MODULES.values())
WRITE_TOOLS = frozenset(
    {
        "watchlist_add",
        "watchlist_remove",
        "watchlist_enable",
        "watchlist_disable",
        "supplier_add",
        "supplier_remove",
        "supplier_delete",
    }
)


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be one of: true, false, 1, 0, yes, no, on, off.")


@dataclass(frozen=True)
class ToolPolicy:
    enabled_modules: frozenset[str]
    enable_write_tools: bool = False

    @classmethod
    def from_environment(cls, enable_write_tools: bool | None = None) -> "ToolPolicy":
        configured = os.getenv("WHITEINTEL_ENABLED_MODULES")
        if configured is None or not configured.strip():
            modules = ALL_MODULES
        else:
            modules = frozenset(item.strip() for item in configured.split(",") if item.strip())
            unknown = modules - ALL_MODULES
            if unknown:
                supported = ", ".join(sorted(ALL_MODULES))
                raise ValueError(
                    f"Unknown WHITEINTEL_ENABLED_MODULES value(s): {', '.join(sorted(unknown))}. "
                    f"Supported modules: {supported}."
                )

        writes_enabled = (
            env_flag("WHITEINTEL_ENABLE_WRITE_TOOLS")
            if enable_write_tools is None
            else enable_write_tools
        )
        return cls(enabled_modules=modules, enable_write_tools=writes_enabled)

    def allows(self, tool_name: str) -> bool:
        module = TOOL_MODULES.get(tool_name)
        if module is None or module not in self.enabled_modules:
            return False
        return self.enable_write_tools or tool_name not in WRITE_TOOLS

    def apply(self, server: FastMCP) -> None:
        for tool_name in TOOL_MODULES:
            if not self.allows(tool_name):
                server.remove_tool(tool_name)
