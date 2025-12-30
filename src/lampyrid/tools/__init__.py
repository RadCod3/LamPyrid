"""
MCP Tools for LamPyrid.

This module coordinates the registration of all MCP tools organized by domain.
"""

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from .accounts import register_tools as register_account_tools
from .budgets import register_tools as register_budget_tools
from .transactions import register_tools as register_transaction_tools


def register_all_tools(mcp: FastMCP, client: FireflyClient) -> None:
	"""
	Register all MCP tools with the FastMCP server.

	This function coordinates tool registration from all domain modules:
	- Account management tools (accounts.py)
	- Transaction management tools (transactions.py)
	- Budget management tools (budgets.py)

	Args:
		mcp: The FastMCP server instance
		client: The FireflyClient instance for API interactions
	"""
	# Import registration functions from each tool module

	# Register tools from each domain
	register_account_tools(mcp, client)
	register_transaction_tools(mcp, client)
	register_budget_tools(mcp, client)
