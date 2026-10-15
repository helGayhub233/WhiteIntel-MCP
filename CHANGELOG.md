# Changelog

All notable changes to WhiteIntel-MCP will be documented in this file.

## [0.6.0] - 2026-10-16

### Added

- Added input-specific investigation workflows to read-only query tool
  descriptions: domain/email-domain, exact IP, hostname, username/email, leak
  IDs, feed search/filter values, metrics, card selectors, and stored entities.
  Guidance covers complementary datasets, provenance-aware merging, client-side
  URL connectivity checks via lightweight CLI HTTP commands (curl/wget), and
  observed raw excerpts; unavailable checks remain unverified and captured
  credential URLs are distinguished from public leak hosts.
- Added unittest coverage for four MCP protocol revisions, full response
  validation, cache hints, and catalog-size budgets.
- Declared jsonschema in the dev dependency group instead of relying on SDK
  transitive dependencies.
- Added `database` as a `username_leaks` source `type`, matching the current
  official API documentation; third-party breach records (with
  `hashed_password`, `database_name`, and `description` fields) can now be
  requested alongside stealer and combolist sources.
- Mirrored the official API Sandbox documentation (10 pages) plus the
  Authentication and Open API Spec overview pages under `docs/`; sandbox
  endpoints live under `https://api.whiteintel.io/sandbox/` and can be reached
  by pointing `WHITEINTEL_BASE_URL` at that prefix.

### Changed

- Replaced repeated tool output schemas with an object skeleton and a vendor
  metadata link to the complete response-schema resource. Server validation
  still uses the complete response model.
- Replaced the private SDK input-schema lookup with its public list_tools API;
  newly added and removed tools are reflected immediately.
- Removed an unused record-count import and marked the legacy SSE transport
  deprecated in CLI help and documentation. Documented the unknown-tool error
  compatibility choice and remaining official Registry publication requirements.
- Updated the MCP SDK requirement, lockfile, and documented baseline to 2.3.0.
- Unified parameter, unknown-tool, and upstream failures with structured error
  codes and identical JSON text/structured content. Validation details omit
  rejected values; protocol errors retain their JSON-RPC semantics.
- Corrected record counts for top-level results, suppliers, audit logs, and
  single/batched leak-ID responses. Conflicting pagination signals now remain
  unknown rather than claiming a complete result.
- Added a 64 KiB public JSON budget and 4096-character string limit. Local
  clipping reports omitted records and requires query refinement before paging.
- Honor the full provider Retry-After across retries and later route/key calls;
  waits over 30 seconds return a rate-limit error instead of retrying early.
- Publish strict inputs, paired-date constraints, bounded positive leak IDs,
  and exact six/eight-digit BIN validation. HTTP failures and malformed success
  flags cannot be reported as successful tool calls.
- Enabled private cache hints for static MCP methods and compacted repeated
  schema documentation, with the complete schema available as a resource.
- Raised the default `WHITEINTEL_UPSTREAM_QPS` pacing from `0.2` to `0.3`
  (about one request every 3.3 seconds) to reduce sequential page-fetch
  latency while keeping a conservative buffer below upstream burst thresholds.
  The standalone last-weak query script guide (`docs/last-weak-query-script.md`)
  now documents the same `0.3` default for its `--qps` option.
- Refreshed mirrored API documentation to the current official revisions:
  username leaks (`database` source type, `remaining_daily_calls` quota
  field), last leaks (documented `sortBy` parameter and sort semantics),
  third-party database (1-second cool-down message, pagination and validation
  notes), leaks by ID (batched empty-result rules), and overall stats
  (per-metric reference with field tables).
- Signature validation doc: clarified that the HMAC base string is the
  `X-Timestamp` value only, and kept the local constant-time comparison
  guidance instead of the current upstream wording.
- Introduced `TODO(sync-with-official)` annotations in mirrored docs and
  request models to track known upstream documentation gaps: the corporate
  endpoint's sandbox-only `database` parameters, the username quota field and
  database field-name inconsistencies, and the required last-leaks `days`
  parameter. Revisit these markers on the next official documentation sync.
- Removed the `mask_password=1` query recommendation and the leaked-credential
  usage restriction from the investigation workflow guidance so MCP responses
  surface raw facts.

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
[0.6.0]: https://github.com/helGayhub233/WhiteIntel-MCP/compare/v0.5.0...v0.6.0
