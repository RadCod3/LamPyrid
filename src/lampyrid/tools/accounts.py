"""Account Management MCP Tools.

This module provides MCP tools for managing Firefly III accounts including
listing, searching, and retrieving account details.
"""

from typing import List

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import (
    Account,
    GetAccountRequest,
    ListAccountRequest,
    SearchAccountRequest,
)
from ..services.accounts import AccountService
from ._annotations import readonly_annotations


def create_accounts_server(client: FireflyClient) -> FastMCP:
    """Create a standalone FastMCP server for account management tools.

    Args:
        client: The FireflyClient instance for API interactions

    Returns:
        FastMCP server instance with account management tools registered

    """
    account_service = AccountService(client)

    accounts_mcp = FastMCP('accounts')

    @accounts_mcp.tool(
        tags={'accounts'},
        annotations=readonly_annotations('List Accounts'),
    )
    async def list_accounts(req: ListAccountRequest) -> List[Account]:
        """Retrieve accounts from Firefly III.

        Use 'asset' for checking/savings accounts, 'expense' for spending accounts, 'revenue' for
        income sources. Essential for finding account IDs before creating transactions.
        """
        return await account_service.list_accounts(req)

    @accounts_mcp.tool(
        tags={'accounts'},
        annotations=readonly_annotations('Get Account'),
    )
    async def get_account(req: GetAccountRequest) -> Account:
        """Retrieve detailed account information including current balance and currency.

        Use this to verify account details before transactions.
        """
        return await account_service.get_account(req)

    @accounts_mcp.tool(
        tags={'accounts'},
        annotations=readonly_annotations('Search Accounts'),
    )
    async def search_accounts(req: SearchAccountRequest) -> List[Account]:
        """Find accounts by partial name matching.

        Useful when you know the account name but not the ID. Supports filtering by account type.
        """
        return await account_service.search_accounts(req)

    return accounts_mcp
