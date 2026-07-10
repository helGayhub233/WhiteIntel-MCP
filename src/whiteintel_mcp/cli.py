"""CLI entry point for WhiteIntel MCP Proxy.

Currently a reserved placeholder — the primary interface is via the
MCP stdio server.  The CLI may be extended later with local debugging
and smoke-test commands.
"""

from __future__ import annotations

import argparse
import sys

from whiteintel_mcp import __version__


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="whiteintel-mcp",
        description="WhiteIntel MCP Proxy — unified threat intelligence data access via MCP.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    # Future subcommands can be added here (e.g. 'smoke', 'health').
    args = parser.parse_args(argv)

    # When invoked without subcommands, print help.
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
