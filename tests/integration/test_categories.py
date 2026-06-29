"""Integration tests for category management tools.

These exercise the category tools against a real Firefly III instance and verify
that categories submitted on transactions are auto-created and that spending
totals are reported for a requested period.
"""

from datetime import datetime, timezone
from typing import List

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from lampyrid.models.lampyrid_models import Account, Category, Transaction


def _month_bounds() -> tuple[str, str]:
    """Return (first-of-month, today) ISO date strings for the current UTC month.

    Uses UTC to stay consistent with the UTC timestamps used when creating the
    test transactions, avoiding month-boundary flakiness in non-UTC timezones.
    """
    today = datetime.now(timezone.utc).date()
    return today.replace(day=1).isoformat(), today.isoformat()


@pytest.mark.asyncio
@pytest.mark.categories
@pytest.mark.integration
async def test_category_auto_created_and_listed(
    mcp_client: Client,
    test_asset_account: Account,
    test_expense_account: str,
    transaction_cleanup: List[str],
):
    """An unknown category submitted on a withdrawal is auto-created and listed."""
    category_name = 'Integration Listed Category'

    result = await mcp_client.call_tool(
        'create_withdrawal',
        {
            'req': {
                'amount': 12.0,
                'description': 'Withdrawal with new category',
                'source_id': test_asset_account.id,
                'destination_name': test_expense_account,
                'category_name': category_name,
                'date': datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    transaction = Transaction.model_validate(result.structured_content)
    assert transaction.id is not None
    transaction_cleanup.append(transaction.id)

    # The transaction carries the category, with a freshly assigned id.
    assert transaction.category_name == category_name
    assert transaction.category_id is not None

    # list_categories returns it as a first-class object.
    listed = await mcp_client.call_tool('list_categories', {})
    categories = [Category.model_validate(c) for c in listed.structured_content['result']]
    names = {c.name for c in categories}
    assert category_name in names


@pytest.mark.asyncio
@pytest.mark.categories
@pytest.mark.integration
async def test_get_category_reports_period_spending(
    mcp_client: Client,
    test_asset_account: Account,
    test_expense_account: str,
    transaction_cleanup: List[str],
):
    """get_category returns spent for a period, and omits it when no range is given."""
    category_name = 'Integration Spending Category'
    amount = 37.5

    create = await mcp_client.call_tool(
        'create_withdrawal',
        {
            'req': {
                'amount': amount,
                'description': 'Withdrawal for spending category',
                'source_id': test_asset_account.id,
                'destination_name': test_expense_account,
                'category_name': category_name,
                'date': datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    transaction = Transaction.model_validate(create.structured_content)
    assert transaction.id is not None
    transaction_cleanup.append(transaction.id)
    category_id = transaction.category_id
    assert category_id is not None

    # With a date range: spent reflects the withdrawal we just made.
    start, end = _month_bounds()
    with_period = await mcp_client.call_tool(
        'get_category',
        {'req': {'id': category_id, 'start_date': start, 'end_date': end}},
    )
    category = Category.model_validate(with_period.structured_content)
    assert category.id == category_id
    assert category.name == category_name
    assert category.spent == amount

    # Without a date range: no spending totals are populated.
    without_period = await mcp_client.call_tool('get_category', {'req': {'id': category_id}})
    bare = Category.model_validate(without_period.structured_content)
    assert bare.spent is None
    assert bare.earned is None


@pytest.mark.asyncio
@pytest.mark.categories
@pytest.mark.integration
async def test_get_category_invalid_id_raises(mcp_client: Client):
    """Requesting a non-existent category id raises an error."""
    with pytest.raises(ToolError):
        await mcp_client.call_tool('get_category', {'req': {'id': '99999999'}})
