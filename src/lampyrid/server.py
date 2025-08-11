from fastmcp import FastMCP
from .clients.firefly import FireflyClient
from .models.firefly_models import AccountArray, AccountTypeFilter

mcp = FastMCP("lampyrid")
_client = FireflyClient()


@mcp.tool()
async def list_accounts() -> AccountArray:
    """List Firefly-III accounts. Provide `type` for filtering."""

    return await _client.list_accounts(type=AccountTypeFilter.asset)
