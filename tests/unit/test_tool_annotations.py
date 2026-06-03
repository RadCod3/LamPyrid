"""Unit tests for MCP tool annotations."""

from unittest.mock import MagicMock

import pytest
from fastmcp import FastMCP
from fastmcp.tools import Tool

from lampyrid.tools.accounts import create_accounts_server
from lampyrid.tools.budgets import create_budgets_server
from lampyrid.tools.insights import create_insights_server
from lampyrid.tools.transactions import create_transactions_server


async def _get_tools(server: FastMCP) -> dict[str, Tool]:
    """Return registered tools keyed by tool name."""
    tools = await server.list_tools()
    return {tool.name: tool for tool in tools}


def _assert_readonly_tool(tool: Tool, title: str) -> None:
    """Assert standard annotations for read-only tools."""
    annotations = tool.annotations

    assert annotations is not None
    assert annotations.title == title
    assert annotations.readOnlyHint is True
    assert annotations.idempotentHint is True
    assert annotations.openWorldHint is False


def _assert_mutating_tool(
    tool: Tool,
    title: str,
    *,
    destructive: bool = False,
    idempotent: bool = False,
) -> None:
    """Assert standard annotations for mutating tools."""
    annotations = tool.annotations

    assert annotations is not None
    assert annotations.title == title
    assert annotations.readOnlyHint is False
    assert annotations.destructiveHint is destructive
    assert annotations.idempotentHint is idempotent
    assert annotations.openWorldHint is False


class TestToolAnnotations:
    """Test MCP annotations exposed by tool servers."""

    @pytest.mark.asyncio
    async def test_accounts_tools_have_readonly_annotations(self):
        """Account tools should be marked as read-only."""
        server = create_accounts_server(MagicMock())
        tools = await _get_tools(server)

        _assert_readonly_tool(tools['list_accounts'], 'List Accounts')
        _assert_readonly_tool(tools['get_account'], 'Get Account')
        _assert_readonly_tool(tools['search_accounts'], 'Search Accounts')

    @pytest.mark.asyncio
    async def test_budget_tools_have_expected_annotations(self):
        """Budget tools should distinguish read-only and mutating operations."""
        server = create_budgets_server(MagicMock())
        tools = await _get_tools(server)

        _assert_readonly_tool(tools['list_budgets'], 'List Budgets')
        _assert_readonly_tool(tools['get_budget'], 'Get Budget')
        _assert_readonly_tool(tools['get_budget_spending'], 'Get Budget Spending')
        _assert_readonly_tool(tools['get_budget_summary'], 'Get Budget Summary')
        _assert_readonly_tool(tools['get_available_budget'], 'Get Available Budget')
        _assert_readonly_tool(tools['list_budget_limits'], 'List Budget Limits')
        _assert_mutating_tool(tools['create_budget'], 'Create Budget')
        _assert_mutating_tool(tools['set_budget_limit'], 'Set Budget Limit', idempotent=True)
        _assert_mutating_tool(tools['delete_budget_limit'], 'Delete Budget Limit', destructive=True)

    @pytest.mark.asyncio
    async def test_insight_tools_have_readonly_annotations(self):
        """Insight tools should be marked as read-only."""
        server = create_insights_server(MagicMock())
        tools = await _get_tools(server)

        _assert_readonly_tool(tools['get_expense_insight'], 'Get Expense Insight')
        _assert_readonly_tool(tools['get_income_insight'], 'Get Income Insight')
        _assert_readonly_tool(tools['get_transfer_insight'], 'Get Transfer Insight')
        _assert_readonly_tool(tools['get_financial_summary'], 'Get Financial Summary')

    @pytest.mark.asyncio
    async def test_transaction_tools_have_expected_annotations(self):
        """Transaction tools should distinguish query, mutating, and destructive operations."""
        server = create_transactions_server(MagicMock())
        tools = await _get_tools(server)

        _assert_mutating_tool(tools['create_withdrawal'], 'Create Withdrawal')
        _assert_mutating_tool(tools['create_deposit'], 'Create Deposit')
        _assert_mutating_tool(tools['create_transfer'], 'Create Transfer')
        _assert_mutating_tool(tools['create_bulk_transactions'], 'Create Bulk Transactions')

        _assert_readonly_tool(tools['get_transaction'], 'Get Transaction')
        _assert_readonly_tool(tools['get_transactions'], 'Get Transactions')
        _assert_readonly_tool(tools['search_transactions'], 'Search Transactions')

        _assert_mutating_tool(
            tools['delete_transaction'],
            'Delete Transaction',
            destructive=True,
        )
        _assert_mutating_tool(tools['update_transaction'], 'Update Transaction')
        _assert_mutating_tool(tools['bulk_update_transactions'], 'Bulk Update Transactions')
