# Changelog

All notable changes to WhiteIntel-MCP will be documented in this file.

## [Unreleased]

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
