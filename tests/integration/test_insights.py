"""Integration tests for insight analysis tools."""

from datetime import date, timedelta

import pytest
from dirty_equals import IsDatetime, IsStr
from fastmcp import Client
from inline_snapshot import snapshot

from lampyrid.models.lampyrid_models import (
    Account,
    Budget,
)


def _get_current_month_dates() -> tuple[date, date]:
    """Get start and end dates for the current month."""
    today = date.today()
    start = today.replace(day=1)
    # End of month
    next_month = start.replace(day=28) + timedelta(days=4)
    end = next_month.replace(day=1) - timedelta(days=1)
    return start, end


# =============================================================================
# Expense Insight Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_expense_insight_total(mcp_client: Client):
    """Test getting total expense insight without grouping."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_expense_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [
                {
                    'id': None,
                    'name': 'Total Expenses',
                    'amount': 145.0,
                    'currency_code': 'USD',
                }
            ],
            'total_expenses': 145.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': None,
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_expense_insight_by_expense_account(mcp_client: Client):
    """Test getting expense insight grouped by expense account (vendor/payee)."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_expense_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'group_by': 'expense_account',
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [
                {
                    'id': IsStr(min_length=1),
                    'name': 'Test Expense',
                    'amount': 115.0,
                    'currency_code': 'USD',
                },
                {
                    'id': IsStr(min_length=1),
                    'name': 'Test Expense 2',
                    'amount': 30.0,
                    'currency_code': 'USD',
                },
            ],
            'total_expenses': 145.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': 'expense_account',
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_expense_insight_by_asset_account(
    mcp_client: Client, test_asset_account: Account
):
    """Test getting expense insight grouped by asset account (source)."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_expense_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'group_by': 'asset_account',
            }
        },
    )
    insight = result.structured_content
    assert insight == snapshot(
        {
            'entries': [
                {
                    'id': IsStr(min_length=1),
                    'name': 'Test Checking',
                    'amount': 120.0,
                    'currency_code': 'USD',
                },
                {
                    'id': IsStr(min_length=1),
                    'name': 'Test Savings',
                    'amount': 25.0,
                    'currency_code': 'USD',
                },
            ],
            'total_expenses': 145.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': 'asset_account',
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_expense_insight_by_budget(mcp_client: Client, test_budget: Budget):
    """Test getting expense insight grouped by budget with unbudgeted expenses."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_expense_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'group_by': 'budget',
                'include_unbudgeted': True,
            }
        },
    )
    insight = result.structured_content
    assert insight == snapshot(
        {
            'entries': [
                {
                    'id': IsStr(min_length=1),
                    'name': 'Test Budget',
                    'amount': 40.0,
                    'currency_code': 'USD',
                },
                {
                    'id': None,
                    'name': 'Unbudgeted',
                    'amount': 105.0,
                    'currency_code': 'USD',
                },
            ],
            'total_expenses': 145.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': 'budget',
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_expense_insight_by_budget_without_unbudgeted(
    mcp_client: Client, test_budget: Budget
):
    """Test getting expense insight by budget without including unbudgeted expenses."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_expense_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'group_by': 'budget',
                'include_unbudgeted': False,
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [{'id': '1', 'name': 'Test Budget', 'amount': 40.0, 'currency_code': 'USD'}],
            'total_expenses': 40.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': 'budget',
        }
    )


# =============================================================================
# Income Insight Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_income_insight_total(mcp_client: Client):
    """Test getting total income insight without grouping."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_income_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [
                {'id': None, 'name': 'Total Income', 'amount': 300.0, 'currency_code': 'USD'}
            ],
            'total_income': 300.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': None,
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_income_insight_by_revenue_account(mcp_client: Client):
    """Test getting income insight grouped by revenue account (source)."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_income_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'group_by': 'revenue_account',
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [
                {'id': '7', 'name': 'Test Revenue', 'amount': 300.0, 'currency_code': 'USD'}
            ],
            'total_income': 300.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': 'revenue_account',
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_income_insight_by_asset_account(mcp_client: Client, test_asset_account: Account):
    """Test getting income insight grouped by asset account (receiving account)."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_income_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'group_by': 'asset_account',
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [
                {'id': '3', 'name': 'Test Savings', 'amount': 100.0, 'currency_code': 'USD'},
                {'id': '1', 'name': 'Test Checking', 'amount': 200.0, 'currency_code': 'USD'},
            ],
            'total_income': 300.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': 'asset_account',
        }
    )


# =============================================================================
# Transfer Insight Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_transfer_insight_total(mcp_client: Client):
    """Test getting total transfer insight without grouping."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_transfer_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [
                {'id': None, 'name': 'Total Transfers', 'amount': 75.0, 'currency_code': 'USD'}
            ],
            'total_transfers': 75.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': None,
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_transfer_insight_by_asset_account(
    mcp_client: Client, test_asset_account: Account
):
    """Test getting transfer insight grouped by asset account with in/out breakdown."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_transfer_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'group_by': 'asset_account',
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [
                {
                    'id': '1',
                    'name': 'Test Checking',
                    'amount': 75.0,
                    'currency_code': 'USD',
                    'amount_in': 0.0,
                    'amount_out': 75.0,
                },
                {
                    'id': '3',
                    'name': 'Test Savings',
                    'amount': 75.0,
                    'currency_code': 'USD',
                    'amount_in': 75.0,
                    'amount_out': 0.0,
                },
            ],
            'total_transfers': 150.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': 'asset_account',
        }
    )


# =============================================================================
# Financial Summary Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_financial_summary(mcp_client: Client):
    """Test getting complete financial summary."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_financial_summary',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    summary = result.structured_content

    assert summary == snapshot(
        {
            'total_expenses': 145.0,
            'total_income': 300.0,
            'total_transfers': 75.0,
            'net_position': 155.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_financial_summary_with_account_filter(
    mcp_client: Client, test_asset_account: Account
):
    """Test getting financial summary filtered by specific account."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_financial_summary',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'account_ids': [int(test_asset_account.id)],
            }
        },
    )
    summary = result.structured_content

    assert summary == snapshot(
        {
            'total_expenses': 120.0,
            'total_income': 200.0,
            'total_transfers': 0.0,
            'net_position': 80.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
        }
    )


# =============================================================================
# Edge Case Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_expense_insight_empty_period(mcp_client: Client):
    """Test getting expense insight for a period with no data."""
    # Use a date range far in the past where there should be no data
    start = date(2000, 1, 1)
    end = date(2000, 1, 31)

    result = await mcp_client.call_tool(
        'get_expense_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [],
            'total_expenses': 0.0,
            'currency_code': 'USD',
            'start_date': '2000-01-01',
            'end_date': '2000-01-31',
            'group_by': None,
        }
    )


@pytest.mark.asyncio
@pytest.mark.insights
@pytest.mark.integration
async def test_get_income_insight_with_account_filter(
    mcp_client: Client, test_asset_account: Account
):
    """Test getting income insight filtered by specific account."""
    start, end = _get_current_month_dates()

    result = await mcp_client.call_tool(
        'get_income_insight',
        {
            'req': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'account_ids': [int(test_asset_account.id)],
            }
        },
    )
    insight = result.structured_content

    assert insight == snapshot(
        {
            'entries': [
                {'id': None, 'name': 'Total Income', 'amount': 200.0, 'currency_code': 'USD'}
            ],
            'total_income': 200.0,
            'currency_code': 'USD',
            'start_date': IsDatetime(iso_string=True),
            'end_date': IsDatetime(iso_string=True),
            'group_by': None,
        }
    )
