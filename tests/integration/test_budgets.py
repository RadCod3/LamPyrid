"""Integration tests for budget management tools."""

from datetime import date, timedelta

import pytest

from lampyrid.clients.firefly import FireflyClient
from lampyrid.models.lampyrid_models import Budget
from tests.fixtures.budgets import (
	make_get_available_budget_request,
	make_get_budget_request,
	make_get_budget_spending_request,
	make_get_budget_summary_request,
	make_list_budgets_request,
)


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_list_budgets_all(firefly_client: FireflyClient):
	"""Test listing all budgets regardless of active status."""
	req = make_list_budgets_request()
	budget_array = await firefly_client.list_budgets(req)

	# Convert to Budget objects
	budgets = [Budget.from_budget_read(budget_read) for budget_read in budget_array.data]

	# Should have at least one budget for testing
	assert len(budgets) > 0

	# All budgets should have required fields
	for budget in budgets:
		assert budget.id is not None
		assert budget.name is not None


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_list_budgets_active_only(firefly_client: FireflyClient):
	"""Test filtering budgets by active status."""
	req = make_list_budgets_request(active=True)
	budget_array = await firefly_client.list_budgets(req)

	# Convert to Budget objects
	budgets = [Budget.from_budget_read(budget_read) for budget_read in budget_array.data]

	# Should have at least one active budget
	assert len(budgets) > 0

	# All budgets should be active
	for budget in budgets:
		assert budget.active is True


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_get_budget(firefly_client: FireflyClient, test_budget: Budget):
	"""Test retrieving a single budget by ID."""
	req = make_get_budget_request(budget_id=test_budget.id)
	budget = await firefly_client.get_budget(req)

	# Should return the same budget
	assert budget.id == test_budget.id
	assert budget.name == test_budget.name


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_get_budget_spending(firefly_client: FireflyClient, test_budget: Budget):
	"""Test getting budget spending analysis for a period."""
	# Use current month
	today = date.today()
	start = today.replace(day=1)
	# End of month
	next_month = start.replace(day=28) + timedelta(days=4)
	end = next_month.replace(day=1) - timedelta(days=1)

	req = make_get_budget_spending_request(budget_id=test_budget.id, start=start, end=end)
	spending = await firefly_client.get_budget_spending(req)

	# Should return spending information
	assert spending.budget_id == test_budget.id
	assert spending.budget_name == test_budget.name
	assert spending.spent >= 0  # Spent should be non-negative
	# budgeted, remaining, and percentage_spent may be None if no limits are set


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_get_budget_summary(firefly_client: FireflyClient):
	"""Test getting comprehensive budget summary."""
	# Use current month
	today = date.today()
	start = today.replace(day=1)
	# End of month
	next_month = start.replace(day=28) + timedelta(days=4)
	end = next_month.replace(day=1) - timedelta(days=1)

	req = make_get_budget_summary_request(start=start, end=end)
	summary = await firefly_client.get_budget_summary(req)

	# Should return summary with at least one budget
	assert len(summary.budgets) > 0

	# Total spent should be sum of all budget spending
	assert summary.total_spent >= 0

	# Check individual budgets
	for budget_spending in summary.budgets:
		assert budget_spending.budget_id is not None
		assert budget_spending.budget_name is not None
		assert budget_spending.spent >= 0


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
@pytest.mark.xfail(
	reason='Firefly III API bug - currency_id returned as int instead of string (issue #43)'
)
async def test_get_available_budget(firefly_client: FireflyClient):
	"""Test getting available budget for a period."""
	# Use current month
	today = date.today()
	start = today.replace(day=1)
	# End of month
	next_month = start.replace(day=28) + timedelta(days=4)
	end = next_month.replace(day=1) - timedelta(days=1)

	req = make_get_available_budget_request(start=start, end=end)
	available = await firefly_client.get_available_budget(req)

	# Should return available budget information
	# amount may be 0 if no available budget is set
	assert available.amount >= 0
	assert available.currency_code is not None
	assert available.start_date == start
	assert available.end_date == end
