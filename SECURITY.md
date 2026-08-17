# Security Policy

## Supported Versions

WhiteIntel-MCP is under active development. Security fixes are applied to the
latest released version only.

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| < 0.5   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in WhiteIntel-MCP, please report it
responsibly:

1. **Do not** open a public GitHub issue.
2. Email `info@whiteintel.io` with a description of the issue, steps to
   reproduce, and potential impact.
3. You should receive an acknowledgment within 48 hours.

## Security Considerations

### API Key Handling

- The WhiteIntel API key is read from the `WHITEINTEL_API_KEY` environment
  variable and is never exposed as an MCP tool parameter.
- API keys are not logged or persisted beyond the process lifetime.

### Remote Binding

- HTTP/SSE transports bind to `127.0.0.1` (loopback) by default.
- Binding to a non-loopback address requires either MCP OAuth
  (`AuthSettings` + `TokenVerifier`) or the explicit
  `WHITEINTEL_MCP_ALLOW_INSECURE_REMOTE=true` flag, which should only be used
  behind a trusted authenticating proxy.

### Write Tool Protection

- Mutating tools (watchlist add/remove/enable/disable, supplier add/remove/delete)
  are disabled by default.
- Enable them only with `WHITEINTEL_ENABLE_WRITE_TOOLS=true` and ensure the
  deployment is protected by authentication.

### Credential Data

- Tool results may contain exposed credentials (passwords) from upstream
  WhiteIntel APIs. Use `mask_password=1` when forwarding results to
  compliance-sensitive downstream systems.
