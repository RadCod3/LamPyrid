"""Category Management MCP Tools.

This module provides MCP tools for reading Firefly III categories. Categories
are auto-created when an unknown category name is submitted on a transaction,
so only read operations are exposed here.
"""

from typing import List

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import Category, GetCategoryRequest
from ..services.categories import CategoryService
from ._annotations import readonly_annotations


def create_categories_server(client: FireflyClient) -> FastMCP:
    """Create a standalone FastMCP server for category management tools.

    Args:
        client: The FireflyClient instance for API interactions

    Returns:
        FastMCP server instance with category management tools registered

    """
    category_service = CategoryService(client)

    categories_mcp = FastMCP('categories')

    @categories_mcp.tool(
        tags={'categories'},
        annotations=readonly_annotations('List Categories'),
    )
    async def list_categories() -> List[Category]:
        """List all categories.

        Categories are a finer-grained classification of transactions (e.g.
        "vegetables", "personal hygiene") that complement budgets. Use this to
        find category IDs/names before assigning them to transactions.
        """
        return await category_service.list_categories()

    @categories_mcp.tool(
        tags={'categories'},
        annotations=readonly_annotations('Get Category'),
    )
    async def get_category(req: GetCategoryRequest) -> Category:
        """Retrieve a single category, optionally with spending for a period.

        Provide start_date and end_date together to include the total spent and
        earned in this category over that period.
        """
        return await category_service.get_category(req)

    return categories_mcp
