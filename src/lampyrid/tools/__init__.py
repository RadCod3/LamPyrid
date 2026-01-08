"""
MCP Tools for LamPyrid.

This module coordinates the composition of all MCP tool servers organized by domain.
Uses FastMCP's native import_server() for static server composition.
"""

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from .accounts import create_accounts_server
from .budgets import create_budgets_server
from .transactions import create_transactions_server


async def compose_all_servers(mcp: FastMCP, client: FireflyClient) -> None:
	"""
	Compose all domain-specific MCP servers into the main server using static composition.

	Args:
		mcp: The main FastMCP server instance
		client: The FireflyClient instance for API interactions
	"""
	# Create standalone servers for each domain
	accounts_server = create_accounts_server(client)
	transactions_server = create_transactions_server(client)
	budgets_server = create_budgets_server(client)

	# Import all servers into the main server without prefixes (static composition)
	await mcp.import_server(accounts_server)
	await mcp.import_server(transactions_server)
	await mcp.import_server(budgets_server)
