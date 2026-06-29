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
        """List all categories, following pagination to return the full set.

        Returns:
                List of categories (without spending totals).

        """
        categories: List[Category] = []
        page = 1
        while True:
            category_array = await self._client.get_categories(page=page)
            categories.extend(Category.from_category_read(cat) for cat in category_array.data)
            pagination = category_array.meta.pagination if category_array.meta else None
            total_pages = pagination.total_pages if pagination else None
            if not category_array.data or not total_pages or page >= total_pages:
                break
            page += 1
        return categories

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
