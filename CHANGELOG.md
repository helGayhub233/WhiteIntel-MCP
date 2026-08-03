# Changelog

All notable changes to WhiteIntel-MCP will be documented in this file.

## [Unreleased]

## [0.4.0] - 2026-08-03

### Changed

- Made conservative local upstream pacing configurable with
  `WHITEINTEL_UPSTREAM_QPS` and keyed it by the actual upstream route.
- Retried HTTP 429 responses once even when `Retry-After` is absent, using the
  documented wait message or a bounded five-second fallback.
- Aligned Threat Feed date bounds and Card Check filters with the current official
  API documentation.
- Hardened non-object JSON handling and classification of HTTP-200 validation
  failures and documented API-key errors.

## [0.3.0] - 2026-07-29

### Added

- Added a JSON Schema 2020-12 `oneOf` contract requiring exactly one of `bin`, `issuer`, or `country` for `card_check`.

### Changed

- Reworked all public tool titles, descriptions, and parameter schemas for TDQS clarity, sibling-tool differentiation, and behavioral transparency.
- Exposed the shared `0.2 QPS` per-endpoint, per-key request pacing in every tool description.
- Updated the README compatibility badge to MCP SDK 2.0.0.
- Removed stale test-only project configuration from the release package.
- Migrated from FastMCP v1 to the official MCP Python SDK 2.0.0 `MCPServer` API.
- Added dual-era support for MCP `2026-07-28` and legacy `2025-11-25` clients.
- Moved HTTP/SSE transport options from the server constructor to `run()` and removed the unsupported `mount_path` CLI option.
- Added the `httpx[socks]` extra so startup works in SOCKS proxy environments.

## [0.2.0] - 2026-07-13

### Added

- Added MCP Tool Annotations for read-only, mutating, idempotent, and destructive operations.
- Added a stable structured response envelope and machine-readable MCP tool error codes.
- Added module allowlisting through `WHITEINTEL_ENABLED_MODULES`.
- Added opt-in write tools through `WHITEINTEL_ENABLE_WRITE_TOOLS`.
- Added standard FastMCP OAuth resource-server injection through `AuthSettings` and `TokenVerifier`.

### Changed

- Write tools are no longer exposed by default.
- Tool schemas now expose endpoint enums, ranges, arrays, booleans, and normalized snake_case names.
- Remote CLI HTTP/SSE binding now fails closed unless protected by an authenticating proxy.
- `Retry-After` waits are capped to prevent a tool call from sleeping indefinitely.

### Compatibility

- Renamed the public `last_leaks.sortBy` argument to `sort_by`.
- Changed `leaks_by_id.query` from a comma-separated string to an integer or integer array.
- Changed Card Check list filters from comma-separated strings to JSON arrays.

### Security

- Added fail-closed remote binding checks and OAuth resource-server integration points.
- Disabled mutating Watchlist and Supplier tools unless explicitly enabled.

## [0.1.0] - 2026-07-10

### Added

- Initial WhiteIntel-MCP FastMCP server.
- Added WhiteIntel credential exposure, threat feed, watchlist, supplier, audit, and card check tools.
- Added Pydantic request validation, upstream HTTP client lifecycle management, and process-local request pacing.
- Added packaged API documentation resources under `whiteintel://docs/{filename}`.

### Changed

- Split watchlist and supplier action-based endpoints into dedicated MCP tools for clearer model selection.
- Unified upstream request pacing at `0.2 QPS` per `(endpoint, apikey)`.
