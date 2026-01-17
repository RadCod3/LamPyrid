"""Integration tests for budget management tools."""

from datetime import date, timedelta

import pytest
from fastmcp import Client
from inline_snapshot import snapshot

from lampyrid.models.lampyrid_models import Budget, BudgetSpending, BudgetSummary


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_list_budgets_all(mcp_client: Client):
	"""Test listing all budgets regardless of active status."""
	result = await mcp_client.call_tool('list_budgets', {'req': {}})
	budgets = result.data

	# Should have at least one budget for testing
	assert len(budgets) > 0

	assert budgets == snapshot(
		[{'id': '1', 'name': 'Test Budget', 'active': True, 'notes': None, 'order': 1}]
	)


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_list_budgets_active_only(mcp_client: Client):
	"""Test filtering budgets by active status."""
	result = await mcp_client.call_tool('list_budgets', {'req': {'active': True}})
	budgets = result.data

	# Should have at least one active budget
	assert len(budgets) > 0

	assert budgets == snapshot(
		[{'id': '1', 'name': 'Test Budget', 'active': True, 'notes': None, 'order': 1}]
	)


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_get_budget(mcp_client: Client, test_budget: Budget):
	"""Test retrieving a single budget by ID."""
	result = await mcp_client.call_tool('get_budget', {'req': {'id': test_budget.id}})
	budget = result.structured_content

	assert budget == snapshot(
		{'id': '1', 'name': 'Test Budget', 'active': True, 'notes': None, 'order': 1}
	)


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_get_budget_spending(mcp_client: Client, test_budget: Budget):
	"""Test getting budget spending analysis for a period."""
	# Use current month
	today = date.today()
	start = today.replace(day=1)
	# End of month
	next_month = start.replace(day=28) + timedelta(days=4)
	end = next_month.replace(day=1) - timedelta(days=1)

	result = await mcp_client.call_tool(
		'get_budget_spending',
		{'req': {'budget_id': test_budget.id, 'start': start.isoformat(), 'end': end.isoformat()}},
	)
	spending = BudgetSpending.model_validate(result.structured_content)

	# Should return spending information
	assert spending.budget_id == test_budget.id
	assert spending.budget_name == test_budget.name
	assert spending.spent >= 0  # Spent should be non-negative
	# budgeted, remaining, and percentage_spent may be None if no limits are set

	# Validate spending structure with snapshot
	assert result.structured_content == snapshot(
		{
			'budget_id': '1',
			'budget_name': 'Test Budget',
			'spent': 0.0,
			'budgeted': None,
			'remaining': None,
			'percentage_spent': None,
		}
	)


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_get_budget_summary(mcp_client: Client):
	"""Test getting comprehensive budget summary."""
	# Use current month
	today = date.today()
	start = today.replace(day=1)
	# End of month
	next_month = start.replace(day=28) + timedelta(days=4)
	end = next_month.replace(day=1) - timedelta(days=1)

	result = await mcp_client.call_tool(
		'get_budget_summary', {'req': {'start': start.isoformat(), 'end': end.isoformat()}}
	)
	summary = BudgetSummary.model_validate(result.structured_content)

	# Should return summary with at least one budget
	assert len(summary.budgets) > 0

	# Total spent should be sum of all budget spending
	assert summary.total_spent >= 0

	# Check individual budgets
	for budget_spending in summary.budgets:
		assert budget_spending.budget_id is not None
		assert budget_spending.budget_name is not None
		assert budget_spending.spent >= 0

	assert result.structured_content == snapshot(
		{
			'budgets': [
				{
					'budget_id': '1',
					'budget_name': 'Test Budget',
					'spent': 0.0,
					'budgeted': None,
					'remaining': None,
					'percentage_spent': None,
				}
			],
			'total_budgeted': None,
			'total_spent': 0.0,
			'total_remaining': None,
			'available_budget': None,
		}
	)


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
@pytest.mark.xfail(
	reason='Firefly III API bug - currency_id returned as int instead of string (issue #43)'
)
async def test_get_available_budget(mcp_client: Client):
	"""Test getting available budget for a period."""
	# Use current month
	today = date.today()
	start = today.replace(day=1)
	# End of month
	next_month = start.replace(day=28) + timedelta(days=4)
	end = next_month.replace(day=1) - timedelta(days=1)

	result = await mcp_client.call_tool(
		'get_available_budget', {'req': {'start': start.isoformat(), 'end': end.isoformat()}}
	)
	available = result.data

	# Should return available budget information
	# amount may be 0 if no available budget is set
	assert available['amount'] >= 0
	assert available['currency_code'] is not None
	assert available['start_date'] == start.isoformat()
	assert available['end_date'] == end.isoformat()
