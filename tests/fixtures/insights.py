"""Test data factories for insight-related tests."""

from datetime import date, timedelta
from typing import List, Literal

from lampyrid.models.lampyrid_models import (
    GetExpenseInsightRequest,
    GetFinancialSummaryRequest,
    GetIncomeInsightRequest,
    GetTransferInsightRequest,
)


def make_get_expense_insight_request(
    start: date | None = None,
    end: date | None = None,
    group_by: Literal['expense_account', 'asset_account', 'budget'] | None = None,
    account_ids: List[int] | None = None,
    budget_ids: List[int] | None = None,
    include_unbudgeted: bool = True,
) -> GetExpenseInsightRequest:
    """Create a GetExpenseInsightRequest for testing."""
    if start is None:
        # Default to current month
        start = date.today().replace(day=1)
    if end is None:
        # Default to end of current month
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1) - timedelta(days=1)

    return GetExpenseInsightRequest(
        start_date=start,
        end_date=end,
        group_by=group_by,
        account_ids=account_ids,
        budget_ids=budget_ids,
        include_unbudgeted=include_unbudgeted,
    )


def make_get_income_insight_request(
    start: date | None = None,
    end: date | None = None,
    group_by: Literal['revenue_account', 'asset_account'] | None = None,
    account_ids: List[int] | None = None,
) -> GetIncomeInsightRequest:
    """Create a GetIncomeInsightRequest for testing."""
    if start is None:
        # Default to current month
        start = date.today().replace(day=1)
    if end is None:
        # Default to end of current month
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1) - timedelta(days=1)

    return GetIncomeInsightRequest(
        start_date=start,
        end_date=end,
        group_by=group_by,
        account_ids=account_ids,
    )


def make_get_transfer_insight_request(
    start: date | None = None,
    end: date | None = None,
    group_by: Literal['asset_account'] | None = None,
    account_ids: List[int] | None = None,
) -> GetTransferInsightRequest:
    """Create a GetTransferInsightRequest for testing."""
    if start is None:
        # Default to current month
        start = date.today().replace(day=1)
    if end is None:
        # Default to end of current month
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1) - timedelta(days=1)

    return GetTransferInsightRequest(
        start_date=start,
        end_date=end,
        group_by=group_by,
        account_ids=account_ids,
    )


def make_get_financial_summary_request(
    start: date | None = None,
    end: date | None = None,
    account_ids: List[int] | None = None,
) -> GetFinancialSummaryRequest:
    """Create a GetFinancialSummaryRequest for testing."""
    if start is None:
        # Default to current month
        start = date.today().replace(day=1)
    if end is None:
        # Default to end of current month
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1) - timedelta(days=1)

    return GetFinancialSummaryRequest(
        start_date=start,
        end_date=end,
        account_ids=account_ids,
    )
