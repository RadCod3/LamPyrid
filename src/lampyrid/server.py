from typing import List
from fastmcp import FastMCP
from .clients.firefly import FireflyClient
from .models.lampyrid_models import Account, ListAccountRequest

mcp = FastMCP("lampyrid")
_client = FireflyClient()


@mcp.tool()
async def list_accounts(req: ListAccountRequest) -> List[Account]:
    """List Firefly-III accounts. Provide `type` for filtering."""
    account_list = await _client.list_accounts(type=req.type)

    accounts: List[Account] = [
        Account.from_account_read(account_read) for account_read in account_list.data
    ]

    return accounts
