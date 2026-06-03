"""Test data factories for budget-related tests."""

from datetime import date, timedelta
from typing import Literal

from lampyrid.models.lampyrid_models import (
    CreateBudgetRequest,
    DeleteBudgetLimitRequest,
    GetAvailableBudgetRequest,
    GetBudgetRequest,
    GetBudgetSpendingRequest,
    GetBudgetSummaryRequest,
    ListBudgetLimitsRequest,
    ListBudgetsRequest,
    SetBudgetLimitRequest,
)


def make_list_budgets_request(active: bool | None = None) -> ListBudgetsRequest:
    """Create a ListBudgetsRequest for testing."""
    return ListBudgetsRequest(active=active)


def make_get_budget_request(budget_id: str) -> GetBudgetRequest:
    """Create a GetBudgetRequest for testing."""
    return GetBudgetRequest(id=budget_id)


def make_get_budget_spending_request(
    budget_id: str, start: date | None = None, end: date | None = None
) -> GetBudgetSpendingRequest:
    """Create a GetBudgetSpendingRequest for testing."""
    if start is None:
        # Default to current month
        start = date.today().replace(day=1)
    if end is None:
        # Default to end of current month
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1) - timedelta(days=1)

    return GetBudgetSpendingRequest(budget_id=budget_id, start_date=start, end_date=end)


def make_get_budget_summary_request(
    start: date | None = None, end: date | None = None
) -> GetBudgetSummaryRequest:
    """Create a GetBudgetSummaryRequest for testing."""
    if start is None:
        # Default to current month
        start = date.today().replace(day=1)
    if end is None:
        # Default to end of current month
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1) - timedelta(days=1)

    return GetBudgetSummaryRequest(start_date=start, end_date=end)


def make_get_available_budget_request(
    start: date | None = None, end: date | None = None
) -> GetAvailableBudgetRequest:
    """Create a GetAvailableBudgetRequest for testing."""
    if start is None:
        # Default to current month
        start = date.today().replace(day=1)
    if end is None:
        # Default to end of current month
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1) - timedelta(days=1)

    return GetAvailableBudgetRequest(start_date=start, end_date=end)


def make_create_budget_request(
    name: str,
    auto_budget_type: Literal['none', 'reset', 'rollover'] | None = None,
    auto_budget_amount: float | None = None,
    auto_budget_period: Literal['daily', 'weekly', 'monthly', 'quarterly', 'half-year', 'yearly']
    | None = None,
    auto_budget_currency_code: str | None = None,
    active: bool = True,
    notes: str | None = None,
) -> CreateBudgetRequest:
    """Create a CreateBudgetRequest for testing."""
    return CreateBudgetRequest(
        name=name,
        auto_budget_type=auto_budget_type,
        auto_budget_amount=auto_budget_amount,
        auto_budget_period=auto_budget_period,
        auto_budget_currency_code=auto_budget_currency_code,
        active=active,
        notes=notes,
    )


def _default_month() -> tuple[date, date]:
    """Return (first, last) day of the current calendar month."""
    start = date.today().replace(day=1)
    next_month = start.replace(day=28) + timedelta(days=4)
    end = next_month.replace(day=1) - timedelta(days=1)
    return start, end


def make_set_budget_limit_request(
    amount: float,
    budget_id: str | None = None,
    budget_name: str | None = None,
    start: date | None = None,
    end: date | None = None,
    currency_code: str | None = None,
    notes: str | None = None,
) -> SetBudgetLimitRequest:
    """Create a SetBudgetLimitRequest for testing (defaults to current month)."""
    if start is None and end is None:
        start, end = _default_month()
    return SetBudgetLimitRequest(
        budget_id=budget_id,
        budget_name=budget_name,
        amount=amount,
        start_date=start,
        end_date=end,
        currency_code=currency_code,
        notes=notes,
    )


def make_list_budget_limits_request(
    budget_id: str | None = None,
    budget_name: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> ListBudgetLimitsRequest:
    """Create a ListBudgetLimitsRequest for testing."""
    return ListBudgetLimitsRequest(
        budget_id=budget_id,
        budget_name=budget_name,
        start_date=start,
        end_date=end,
    )


def make_delete_budget_limit_request(
    budget_id: str | None = None,
    budget_name: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> DeleteBudgetLimitRequest:
    """Create a DeleteBudgetLimitRequest for testing (defaults to current month)."""
    if start is None and end is None:
        start, end = _default_month()
    return DeleteBudgetLimitRequest(
        budget_id=budget_id,
        budget_name=budget_name,
        start_date=start,
        end_date=end,
    )
