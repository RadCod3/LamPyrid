"""Category Service for LamPyrid.

This service handles category-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

from typing import List

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import Category, GetCategoryRequest


class CategoryService:
    """Service for reading Firefly III categories.

    Categories are auto-created when an unknown category name is submitted on a
    transaction, so this service exposes read operations only.
    """

    def __init__(self, client: FireflyClient) -> None:
        """Initialize the category service with a FireflyClient instance."""
        self._client = client

    async def list_categories(self) -> List[Category]:
        """List all categories.

        Returns:
                List of categories (without spending totals).

        """
        category_array = await self._client.get_categories()
        return [Category.from_category_read(cat) for cat in category_array.data]

    async def get_category(self, req: GetCategoryRequest) -> Category:
        """Get a single category, optionally with spending/earning totals for a period.

        Args:
                req: Request containing the category ID and optional date range

        Returns:
                Category details, including spent/earned when a date range is provided.

        """
        category_single = await self._client.get_category(
            req.id, start_date=req.start_date, end_date=req.end_date
        )
        return Category.from_category_read(category_single.data)
