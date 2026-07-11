# Changelog

All notable changes to WhiteIntel-MCP will be documented in this file.

## [0.1.0] - 2026-07-10

### Added

- Initial WhiteIntel-MCP FastMCP server.
- Added WhiteIntel credential exposure, threat feed, watchlist, supplier, audit, and card check tools.
- Added Pydantic request validation, upstream HTTP client lifecycle management, and process-local request pacing.
- Added packaged API documentation resources under `whiteintel://docs/{filename}`.

### Changed

- Split watchlist and supplier action-based endpoints into dedicated MCP tools for clearer model selection.
- Unified upstream request pacing at `0.2 QPS` per `(endpoint, apikey)`.
