"""Tag Service for LamPyrid.

This service handles tag-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

from typing import List

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import GetTagRequest, Tag


class TagService:
    """Service for reading Firefly III tags.

    Tags are auto-created when an unknown tag is submitted on a transaction, so
    this service exposes read operations only.
    """

    def __init__(self, client: FireflyClient) -> None:
        """Initialize the tag service with a FireflyClient instance."""
        self._client = client

    async def list_tags(self) -> List[Tag]:
        """List all tags.

        Returns:
                List of tags.

        """
        tag_array = await self._client.get_tags()
        return [Tag.from_tag_read(tag) for tag in tag_array.data]

    async def get_tag(self, req: GetTagRequest) -> Tag:
        """Get a single tag by name or ID.

        Args:
                req: Request containing the tag name or numeric ID

        Returns:
                Tag details.

        """
        tag_single = await self._client.get_tag(req.tag)
        return Tag.from_tag_read(tag_single.data)
