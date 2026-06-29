"""MCP Tools for LamPyrid.

This module coordinates the composition of all MCP tool servers organized by domain.
Uses FastMCP's native mount() for static server composition.
"""

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from .accounts import create_accounts_server
from .budgets import create_budgets_server
from .categories import create_categories_server
from .insights import create_insights_server
from .rules import create_rules_server
from .tags import create_tags_server
from .transactions import create_transactions_server


def compose_all_servers(mcp: FastMCP, client: FireflyClient) -> None:
    """Compose all domain-specific MCP servers into the main server using static composition.

    Args:
            mcp: The main FastMCP server instance
            client: The FireflyClient instance for API interactions

    """
    # Create standalone servers for each domain
    accounts_server = create_accounts_server(client)
    transactions_server = create_transactions_server(client)
    budgets_server = create_budgets_server(client)
    categories_server = create_categories_server(client)
    tags_server = create_tags_server(client)
    insights_server = create_insights_server(client)
    rules_server = create_rules_server(client)

    # Mount all servers into the main server without namespaces (static composition)
    mcp.mount(accounts_server)
    mcp.mount(transactions_server)
    mcp.mount(budgets_server)
    mcp.mount(categories_server)
    mcp.mount(tags_server)
    mcp.mount(insights_server)
    mcp.mount(rules_server)
