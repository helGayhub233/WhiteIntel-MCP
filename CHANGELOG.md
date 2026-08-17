# Changelog

All notable changes to WhiteIntel-MCP will be documented in this file.

## [0.5.0] - 2026-08-17

### Added

- Added `glama.json` for Glama registry metadata and maintainer declaration.
- Added `SECURITY.md` documenting API key handling, remote binding, write tool
  protection, and credential data considerations.
- Added `mcp-name` ownership marker to README for MCP Registry verification.

### Changed

- Clarified `consumer_leaks` tool description: now explicitly states it matches
  the URL where credentials were captured (site-level domain match) and directs
  callers to use `corporate_leaks` alongside for full exposure coverage.
- Clarified `corporate_leaks` tool description: now explicitly states it matches
  the username's email suffix (email-domain match) and warns about false
  positives on short or generic domains.
- Updated `last_leaks` tool description to state it returns both consumer and
  corporate records in a single call.
- Reworked README installation section: renamed uvx heading to "一键安装", added
  uv prerequisite instructions, version-pinning guidance with `--from`, and a
  pipx installation alternative.
- Replaced ambiguous "（需启用写工具）" labels in README tool table with
  "（默认关闭）" and added a dedicated "启用写工具" section with CLI/client
  config examples, a write-tool risk table, and HTTP authorization notes.
- Reorganized README structure: numbered installation steps (1. install uv →
  2. configure client), consolidated all config into a dedicated section
  (env vars with default-value column, write tools, module scoping), moved
  alternative install methods below the main flow, and renamed "发布验证" to
  "开发" with compile/test/build commands.
- Standardized documentation examples on IANA-reserved domains and documentation
  IP ranges so examples cannot identify real organizations or infrastructure.

### Removed

- Removed the empty `src/whiteintel_mcp/tools/` package (only contained a
  docstring `__init__.py` with no implementation).

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

[0.5.0]: https://github.com/helGayhub233/WhiteIntel-MCP/compare/v0.4.0...v0.5.0
