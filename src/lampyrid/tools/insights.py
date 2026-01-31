"""Insight MCP Tools.

This module provides MCP tools for financial insights and analytics
including expense, income, and transfer analysis with optional grouping.
"""

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import (
    ExpenseInsightResult,
    FinancialSummary,
    GetExpenseInsightRequest,
    GetFinancialSummaryRequest,
    GetIncomeInsightRequest,
    GetTransferInsightRequest,
    IncomeInsightResult,
    TransferInsightResult,
)
from ..services.insights import InsightService


def create_insights_server(client: FireflyClient) -> FastMCP:
    """Create a standalone FastMCP server for insight analysis tools.

    Args:
        client: The FireflyClient instance for API interactions

    Returns:
        FastMCP server instance with insight tools registered

    """
    insight_service = InsightService(client)

    insights_mcp = FastMCP('insights')

    @insights_mcp.tool(tags={'insights', 'expenses', 'analysis'})
    async def get_expense_insight(req: GetExpenseInsightRequest) -> ExpenseInsightResult:
        """Analyze expenses for a time period with optional grouping.

        Get total expenses or break them down by expense account (vendor/payee),
        asset account (source), or budget. When grouping by budget, optionally
        includes unbudgeted expenses as a separate entry.

        Use cases:
        - See total spending for a month
        - Identify top expense categories/vendors
        - Track which accounts have the most outflow
        - Analyze budget utilization vs unbudgeted spending
        """
        return await insight_service.get_expense_insight(req)

    @insights_mcp.tool(tags={'insights', 'income', 'analysis'})
    async def get_income_insight(req: GetIncomeInsightRequest) -> IncomeInsightResult:
        """Analyze income for a time period with optional grouping.

        Get total income or break it down by revenue account (source)
        or asset account (receiving account).

        Use cases:
        - See total income for a month
        - Identify income sources
        - Track which accounts receive the most income
        """
        return await insight_service.get_income_insight(req)

    @insights_mcp.tool(tags={'insights', 'transfers', 'analysis'})
    async def get_transfer_insight(req: GetTransferInsightRequest) -> TransferInsightResult:
        """Analyze transfers for a time period with optional account breakdown.

        Get total transfers or break them down by asset account with
        in/out amounts for each account.

        Use cases:
        - See total transfer activity
        - Understand money flow between accounts
        - Track savings/investment transfers
        """
        return await insight_service.get_transfer_insight(req)

    @insights_mcp.tool(tags={'insights', 'summary', 'analysis'})
    async def get_financial_summary(req: GetFinancialSummaryRequest) -> FinancialSummary:
        """Get a complete financial overview for a time period.

        Returns expense, income, and transfer totals along with net position
        (income minus expenses). Makes parallel API calls for efficiency.

        Use cases:
        - Quick financial health check
        - Monthly/yearly overview
        - Dashboard summary data
        """
        return await insight_service.get_financial_summary(req)

    return insights_mcp
