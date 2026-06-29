"""Tag Management MCP Tools.

This module provides MCP tools for reading Firefly III tags. Tags are
auto-created when an unknown tag is submitted on a transaction, so only read
operations are exposed here.
"""

from typing import List

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import GetTagRequest, Tag
from ..services.tags import TagService
from ._annotations import readonly_annotations


def create_tags_server(client: FireflyClient) -> FastMCP:
    """Create a standalone FastMCP server for tag management tools.

    Args:
        client: The FireflyClient instance for API interactions

    Returns:
        FastMCP server instance with tag management tools registered

    """
    tag_service = TagService(client)

    tags_mcp = FastMCP('tags')

    @tags_mcp.tool(
        tags={'tags'},
        annotations=readonly_annotations('List Tags'),
    )
    async def list_tags() -> List[Tag]:
        """List all tags.

        Tags are cross-cutting labels that group transactions across budgets,
        categories, and time (e.g. a trip, a project, a tax year). Use this to
        discover existing tags before assigning or searching by them.
        """
        return await tag_service.list_tags()

    @tags_mcp.tool(
        tags={'tags'},
        annotations=readonly_annotations('Get Tag'),
    )
    async def get_tag(req: GetTagRequest) -> Tag:
        """Retrieve a single tag by its name or numeric ID."""
        return await tag_service.get_tag(req)

    return tags_mcp
