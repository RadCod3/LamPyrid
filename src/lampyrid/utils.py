"""Custom HTTP routes and utilities for LamPyrid MCP server.

This module provides custom HTTP route handlers that are served at the root level,
alongside the MCP protocol endpoints.
"""

from importlib.resources import files
from pathlib import Path

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse


def get_assets_path(filename: str) -> Path:
    """Get path to an asset file bundled with the package."""
    asset_resource = files('lampyrid').joinpath('assets', filename)
    return Path(str(asset_resource))


async def serve_favicon(request: Request):
    """Serve favicon.ico file at the root level."""
    favicon_path = get_assets_path('favicon.ico')
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type='image/x-icon')
    return JSONResponse({'error': 'Not found'}, status_code=404)


def register_custom_routes(mcp: FastMCP) -> None:
    """Register custom HTTP routes with the FastMCP server.

    These routes are served at the root level (e.g., /favicon.ico),
    not nested under the MCP protocol path (e.g., /mcp).

    Args:
            mcp: The FastMCP server instance

    """
    # Register favicon route
    mcp.custom_route('/favicon.ico', methods=['GET'])(serve_favicon)
