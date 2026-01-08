"""
Account Management MCP Tools.

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


def create_accounts_server(client: FireflyClient) -> FastMCP:
	"""
	Create a standalone FastMCP server for account management tools.

	Args:
		client: The FireflyClient instance for API interactions

	Returns:
		FastMCP server instance with account management tools registered
	"""
	accounts_mcp = FastMCP('accounts')

	@accounts_mcp.tool(tags={'accounts'})
	async def list_accounts(req: ListAccountRequest) -> List[Account]:
		"""Retrieve accounts from Firefly III. Use 'asset' for checking/savings accounts, 'expense' for spending accounts, 'revenue' for income sources. Essential for finding account IDs before creating transactions."""
		account_list = await client.list_accounts(type=req.type)

		accounts: List[Account] = [
			Account.from_account_read(account_read) for account_read in account_list.data
		]

		return accounts

	@accounts_mcp.tool(tags={'accounts'})
	async def get_account(req: GetAccountRequest) -> Account:
		"""Retrieve detailed account information including current balance and currency. Use this to verify account details before transactions."""
		return await client.get_account(req)

	@accounts_mcp.tool(tags={'accounts'})
	async def search_accounts(req: SearchAccountRequest) -> List[Account]:
		"""Find accounts by partial name matching. Useful when you know the account name but not the ID. Supports filtering by account type."""
		account_list = await client.search_accounts(req)

		accounts: List[Account] = [
			Account.from_account_read(account_read) for account_read in account_list.data
		]

		return accounts

	return accounts_mcp
