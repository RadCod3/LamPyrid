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


def register_tools(mcp: FastMCP, client: FireflyClient) -> None:
	"""
	Register account management tools with the FastMCP server.

	Args:
		mcp: The FastMCP server instance
		client: The FireflyClient instance for API interactions
	"""

	@mcp.tool(tags={'accounts'})
	async def list_accounts(req: ListAccountRequest) -> List[Account]:  # pyright: ignore[reportUnusedFunction]
		"""Retrieve accounts from Firefly III. Use 'asset' for checking/savings accounts, 'expense' for spending accounts, 'revenue' for income sources. Essential for finding account IDs before creating transactions."""
		account_list = await client.list_accounts(type=req.type)

		accounts: List[Account] = [
			Account.from_account_read(account_read) for account_read in account_list.data
		]

		return accounts

	@mcp.tool(tags={'accounts'})
	async def get_account(req: GetAccountRequest) -> Account:  # pyright: ignore[reportUnusedFunction]
		"""Retrieve detailed account information including current balance and currency. Use this to verify account details before transactions."""
		return await client.get_account(req)

	@mcp.tool(tags={'accounts'})
	async def search_accounts(req: SearchAccountRequest) -> List[Account]:  # pyright: ignore[reportUnusedFunction]
		"""Find accounts by partial name matching. Useful when you know the account name but not the ID. Supports filtering by account type."""
		account_list = await client.search_accounts(req)

		accounts: List[Account] = [
			Account.from_account_read(account_read) for account_read in account_list.data
		]

		return accounts
