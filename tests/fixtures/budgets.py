"""Test data factories for budget-related tests."""

from datetime import date, timedelta

from lampyrid.models.lampyrid_models import (
    GetAvailableBudgetRequest,
    GetBudgetRequest,
    GetBudgetSpendingRequest,
    GetBudgetSummaryRequest,
    ListBudgetsRequest,
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
