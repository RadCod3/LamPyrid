"""Integration tests for budget management tools."""

from datetime import date, timedelta
from typing import List

import pytest
from dirty_equals import IsInt, IsStr
from fastmcp import Client
from inline_snapshot import snapshot

from lampyrid.models.lampyrid_models import (
    AvailableBudget,
    Budget,
    BudgetLimit,
    BudgetSpending,
    BudgetSummary,
)


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_list_budgets_all(mcp_client: Client):
    """Test listing all budgets regardless of active status."""
    result = await mcp_client.call_tool('list_budgets', {'req': {}})
    assert result.structured_content is not None
    budgets = result.structured_content['result']

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
    assert result.structured_content is not None
    budgets = result.structured_content['result']

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
        {
            'req': {
                'budget_id': test_budget.id,
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
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
        'get_budget_summary',
        {'req': {'start_date': start.isoformat(), 'end_date': end.isoformat()}},
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
async def test_get_available_budget(mcp_client: Client):
    """Test getting available budget for a period."""
    # Use current month
    today = date.today()
    start = today.replace(day=1)
    # End of month
    next_month = start.replace(day=28) + timedelta(days=4)
    end = next_month.replace(day=1) - timedelta(days=1)

    result = await mcp_client.call_tool(
        'get_available_budget',
        {'req': {'start_date': start.isoformat(), 'end_date': end.isoformat()}},
    )
    available = AvailableBudget.model_validate(result.structured_content)

    # Should return available budget information
    # amount may be 0 if no available budget is set
    assert available.amount >= 0
    assert available.currency_code is not None
    assert available.start_date.isoformat() == start.isoformat()
    assert available.end_date.isoformat() == end.isoformat()


# =============================================================================
# create_budget Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_create_budget_simple(mcp_client: Client, budget_cleanup: List[str]):
    """Test creating a basic budget with just a name."""
    result = await mcp_client.call_tool('create_budget', {'req': {'name': 'Test Created Budget'}})
    budget = Budget.model_validate(result.structured_content)
    budget_cleanup.append(budget.id)

    assert budget.model_dump() == snapshot(
        {
            'id': IsStr(min_length=1),
            'name': 'Test Created Budget',
            'active': True,
            'notes': None,
            'order': IsInt(ge=1),
        }
    )


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_create_budget_with_auto_budget(mcp_client: Client, budget_cleanup: List[str]):
    """Test creating a budget with auto-budget settings."""
    result = await mcp_client.call_tool(
        'create_budget',
        {
            'req': {
                'name': 'Test Auto Budget',
                'auto_budget_type': 'reset',
                'auto_budget_amount': 500.0,
                'auto_budget_period': 'monthly',
                'auto_budget_currency_code': 'USD',
            }
        },
    )
    budget = Budget.model_validate(result.structured_content)
    budget_cleanup.append(budget.id)

    assert budget.model_dump() == snapshot(
        {
            'id': IsStr(min_length=1),
            'name': 'Test Auto Budget',
            'active': True,
            'notes': None,
            'order': IsInt(ge=1),
        }
    )


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_create_budget_with_notes_inactive(mcp_client: Client, budget_cleanup: List[str]):
    """Test creating an inactive budget with notes."""
    result = await mcp_client.call_tool(
        'create_budget',
        {
            'req': {
                'name': 'Test Inactive Budget',
                'notes': 'This is a test budget with notes',
                'active': False,
            }
        },
    )
    budget = Budget.model_validate(result.structured_content)
    budget_cleanup.append(budget.id)

    assert budget.model_dump() == snapshot(
        {
            'id': IsStr(min_length=1),
            'name': 'Test Inactive Budget',
            'active': False,
            'notes': 'This is a test budget with notes',
            'order': IsInt(ge=1),
        }
    )


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_create_budget_rollover(mcp_client: Client, budget_cleanup: List[str]):
    """Test creating a budget with rollover auto-budget type."""
    result = await mcp_client.call_tool(
        'create_budget',
        {
            'req': {
                'name': 'Test Rollover Budget',
                'auto_budget_type': 'rollover',
                'auto_budget_amount': 300.0,
                'auto_budget_period': 'monthly',
                'notes': 'Rollover unused balance to next month',
            }
        },
    )
    budget = Budget.model_validate(result.structured_content)
    budget_cleanup.append(budget.id)

    assert budget.model_dump() == snapshot(
        {
            'id': IsStr(min_length=1),
            'name': 'Test Rollover Budget',
            'active': True,
            'notes': 'Rollover unused balance to next month',
            'order': IsInt(ge=1),
        }
    )


# =============================================================================
# Budget Limit Tests (set / list / delete)
# =============================================================================


def _current_month() -> tuple[date, date]:
    """Return (first, last) day of the current calendar month."""
    start = date.today().replace(day=1)
    next_month = start.replace(day=28) + timedelta(days=4)
    end = next_month.replace(day=1) - timedelta(days=1)
    return start, end


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_set_budget_limit_creates(
    mcp_client: Client, test_budget: Budget, budget_limit_cleanup: List[tuple[str, str]]
):
    """Setting a limit on a budget with no existing limit creates one."""
    start, end = _current_month()

    result = await mcp_client.call_tool(
        'set_budget_limit',
        {
            'req': {
                'budget_id': test_budget.id,
                'amount': 500.0,
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    limit = BudgetLimit.model_validate(result.structured_content)
    budget_limit_cleanup.append((limit.budget_id, limit.id))

    assert limit.id is not None
    assert limit.budget_id == test_budget.id
    assert limit.amount == 500.0
    assert limit.start_date == start
    assert limit.end_date == end


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_set_budget_limit_updates(
    mcp_client: Client, test_budget: Budget, budget_limit_cleanup: List[tuple[str, str]]
):
    """Setting a limit twice for the same period updates it (upsert, no duplicate)."""
    start, end = _current_month()
    period = {'start_date': start.isoformat(), 'end_date': end.isoformat()}

    first = await mcp_client.call_tool(
        'set_budget_limit',
        {'req': {'budget_id': test_budget.id, 'amount': 300.0, **period}},
    )
    first_limit = BudgetLimit.model_validate(first.structured_content)
    budget_limit_cleanup.append((first_limit.budget_id, first_limit.id))

    second = await mcp_client.call_tool(
        'set_budget_limit',
        {'req': {'budget_id': test_budget.id, 'amount': 650.0, **period}},
    )
    second_limit = BudgetLimit.model_validate(second.structured_content)
    budget_limit_cleanup.append((second_limit.budget_id, second_limit.id))

    assert second_limit.amount == 650.0

    # Upsert: only one limit should exist for this period
    listed = await mcp_client.call_tool(
        'list_budget_limits',
        {'req': {'budget_id': test_budget.id, **period}},
    )
    limits = listed.structured_content['result']
    assert len(limits) == 1
    assert limits[0]['amount'] == 650.0


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_set_budget_limit_by_name(
    mcp_client: Client, test_budget: Budget, budget_limit_cleanup: List[tuple[str, str]]
):
    """A budget limit can be set by referencing the budget by name."""
    start, end = _current_month()

    result = await mcp_client.call_tool(
        'set_budget_limit',
        {
            'req': {
                'budget_name': test_budget.name,
                'amount': 450.0,
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    limit = BudgetLimit.model_validate(result.structured_content)
    budget_limit_cleanup.append((limit.budget_id, limit.id))

    assert limit.budget_id == test_budget.id
    assert limit.amount == 450.0


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_list_budget_limits(
    mcp_client: Client, test_budget: Budget, budget_limit_cleanup: List[tuple[str, str]]
):
    """Listing budget limits returns a previously created limit."""
    start, end = _current_month()

    created = await mcp_client.call_tool(
        'set_budget_limit',
        {
            'req': {
                'budget_id': test_budget.id,
                'amount': 250.0,
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    limit = BudgetLimit.model_validate(created.structured_content)
    budget_limit_cleanup.append((limit.budget_id, limit.id))

    listed = await mcp_client.call_tool(
        'list_budget_limits', {'req': {'budget_id': test_budget.id}}
    )
    limits = listed.structured_content['result']
    assert any(item['id'] == limit.id and item['amount'] == 250.0 for item in limits)


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_budget_spending_reflects_limit(
    mcp_client: Client, test_budget: Budget, budget_limit_cleanup: List[tuple[str, str]]
):
    """After setting a limit, get_budget_spending reports budgeted/remaining."""
    start, end = _current_month()
    period = {'start_date': start.isoformat(), 'end_date': end.isoformat()}

    created = await mcp_client.call_tool(
        'set_budget_limit',
        {'req': {'budget_id': test_budget.id, 'amount': 1000.0, **period}},
    )
    limit = BudgetLimit.model_validate(created.structured_content)
    budget_limit_cleanup.append((limit.budget_id, limit.id))

    spending_result = await mcp_client.call_tool(
        'get_budget_spending',
        {'req': {'budget_id': test_budget.id, **period}},
    )
    spending = BudgetSpending.model_validate(spending_result.structured_content)

    assert spending.budgeted == 1000.0
    assert spending.remaining is not None
    assert spending.percentage_spent is not None


@pytest.mark.asyncio
@pytest.mark.budgets
@pytest.mark.integration
async def test_delete_budget_limit(mcp_client: Client, test_budget: Budget):
    """Deleting a budget limit removes it for the period."""
    start, end = _current_month()
    period = {'start_date': start.isoformat(), 'end_date': end.isoformat()}

    await mcp_client.call_tool(
        'set_budget_limit',
        {'req': {'budget_id': test_budget.id, 'amount': 200.0, **period}},
    )

    deleted = await mcp_client.call_tool(
        'delete_budget_limit', {'req': {'budget_id': test_budget.id, **period}}
    )
    assert deleted.structured_content['result'] is True

    listed = await mcp_client.call_tool(
        'list_budget_limits',
        {'req': {'budget_id': test_budget.id, **period}},
    )
    limits = listed.structured_content['result']
    assert all(not (date.fromisoformat(item['start_date']) == start) for item in limits)
