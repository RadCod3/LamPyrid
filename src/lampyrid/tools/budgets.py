"""Budget Management MCP Tools.

This module provides MCP tools for managing Firefly III budgets including
listing, retrieving, and analyzing budget performance and spending.
"""

from typing import List

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import (
	AvailableBudget,
	Budget,
	BudgetSpending,
	BudgetSummary,
	GetAvailableBudgetRequest,
	GetBudgetRequest,
	GetBudgetSpendingRequest,
	GetBudgetSummaryRequest,
	ListBudgetsRequest,
)
from ..services.budgets import BudgetService


def create_budgets_server(client: FireflyClient) -> FastMCP:
	budget_service = BudgetService(client)
	"""
	Create a standalone FastMCP server for budget management tools.

	Args:
		client: The FireflyClient instance for API interactions

	Returns:
		FastMCP server instance with budget management tools registered
	"""
	budgets_mcp = FastMCP('budgets')

	@budgets_mcp.tool(tags={'budgets'})
	async def list_budgets(req: ListBudgetsRequest) -> List[Budget]:
		"""Retrieve your budgets for expense tracking and financial planning. Filter by active status to see current or all budgets."""
		return await budget_service.list_budgets(req)

	@budgets_mcp.tool(tags={'budgets'})
	async def get_budget(req: GetBudgetRequest) -> Budget:
		"""Retrieve detailed budget information including name, status, and notes. Use this to verify budget details before assigning transactions."""
		return await budget_service.get_budget(req)

	@budgets_mcp.tool(tags={'budgets', 'analysis'})
	async def get_budget_spending(req: GetBudgetSpendingRequest) -> BudgetSpending:
		"""Analyze spending against a budget including amount spent, remaining budget, and percentage used. Essential for budget monitoring and overspending alerts."""
		return await budget_service.get_budget_spending(req)

	@budgets_mcp.tool(tags={'budgets', 'analysis'})
	async def get_budget_summary(req: GetBudgetSummaryRequest) -> BudgetSummary:
		"""Comprehensive overview of all budget performance with totals and spending analysis. Perfect for monthly reviews and financial dashboards."""
		return await budget_service.get_budget_summary(req)

	@budgets_mcp.tool(tags={'budgets', 'analysis'})
	async def get_available_budget(req: GetAvailableBudgetRequest) -> AvailableBudget:
		"""Check unallocated budget available for new budgets or unexpected expenses. Shows money set aside but not assigned to specific budgets."""
		return await budget_service.get_available_budget(req)

	return budgets_mcp
