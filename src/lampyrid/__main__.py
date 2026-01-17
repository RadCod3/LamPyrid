"""Main entry point for the LamPyrid MCP server."""

from .config import settings
from .server import mcp


def main() -> None:
    """Initialize and run the MCP server based on configuration settings."""
    # Support both stdio (for local development) and http (for containerized deployment)
    # Configuration is managed through settings (from .env or environment variables)
    if settings.mcp_transport == 'http':
        # HTTP mode for containerized deployment
        mcp.run(transport='streamable-http', host=settings.mcp_host, port=settings.mcp_port)
    elif settings.mcp_transport == 'sse':
        # SSE mode for real-time updates
        mcp.run(transport='sse', host=settings.mcp_host, port=settings.mcp_port)
    else:
        # Default stdio mode for local development
        mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
