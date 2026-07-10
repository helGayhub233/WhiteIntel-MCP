from mcp.server.fastmcp import FastMCP

from whiteintel_mcp.server import create_server


def test_create_server_returns_fastmcp_instance():
    server = create_server()

    assert isinstance(server, FastMCP)
