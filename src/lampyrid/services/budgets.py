"""Budget Service for LamPyrid.

This service handles budget-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

from datetime import date
from typing import List

from ..clients.firefly import FireflyClient
from ..models.firefly_models import (
    AutoBudgetPeriod,
    AutoBudgetPeriodEnum,
    AutoBudgetType,
    AutoBudgetTypeEnum,
    BudgetStore,
)
from ..models.lampyrid_models import (
    AvailableBudget,
    Budget,
    BudgetSpending,
    BudgetSummary,
    CreateBudgetRequest,
    GetAvailableBudgetRequest,
    GetBudgetRequest,
    GetBudgetSpendingRequest,
    GetBudgetSummaryRequest,
    ListBudgetsRequest,
)


class BudgetService:
    """Service for managing Firefly III budgets.

    This service provides a high-level interface for budget operations,
    handling spending calculations, aggregations, and multi-call orchestration
    while delegating HTTP operations to the FireflyClient.
    """

    def __init__(self, client: FireflyClient) -> None:
        """Initialize the budget service with a FireflyClient instance."""
        self._client = client

    async def list_budgets(self, req: ListBudgetsRequest) -> List[Budget]:
        """List budgets with optional active status filtering.

        Args:
                req: Request containing active status filter

        Returns:
                List of budgets matching the filter criteria

        """
        budget_array = await self._client.get_budgets()

        # Apply active filter if provided
        budgets_data = budget_array.data
        if req.active is not None:
            budgets_data = [x for x in budgets_data if x.attributes.active == req.active]

        return [Budget.from_budget_read(budget_read) for budget_read in budgets_data]

    async def get_budget(self, req: GetBudgetRequest) -> Budget:
        """Get detailed information for a single budget.

        Args:
                req: Request containing the budget ID

        Returns:
                Budget details

        """
        budget_single = await self._client.get_budget(req.id)
        return Budget.from_budget_read(budget_single.data)

    async def get_budget_spending(self, req: GetBudgetSpendingRequest) -> BudgetSpending:
        """Get spending analysis for a specific budget and time period.

        This method orchestrates multiple API calls to calculate budget spending,
        aggregating data from budget limits and performing calculations for
        spent amounts, remaining budget, and percentage used.

        Args:
                req: Request containing budget ID and time period

        Returns:
                Budget spending analysis with calculations

        """
        # Get budget info first
        budget_single = await self._client.get_budget(req.budget_id)
        budget_name = budget_single.data.attributes.name

        # Get spending data from budget limits endpoint
        limits_array = await self._client.get_budget_limits(
            req.budget_id, req.start_date, req.end_date
        )

        # Calculate spending from limits data
        spent = 0.0
        budgeted = None

        for limit in limits_array.data:
            if limit.attributes.spent:
                for spent_entry in limit.attributes.spent:
                    if spent_entry.sum:
                        spent += abs(float(spent_entry.sum))

            # amount is still a string field
            if limit.attributes.amount:
                if budgeted is None:
                    budgeted = 0.0
                budgeted += float(limit.attributes.amount)

        remaining = (budgeted - spent) if budgeted is not None else None
        percentage_spent = (spent / budgeted * 100) if budgeted and budgeted > 0 else None

        return BudgetSpending(
            budget_id=req.budget_id,
            budget_name=budget_name,
            spent=spent,
            budgeted=budgeted,
            remaining=remaining,
            percentage_spent=percentage_spent,
        )

    async def get_budget_summary(self, req: GetBudgetSummaryRequest) -> BudgetSummary:
        """Get comprehensive summary of all budgets with spending information.

        This method orchestrates multiple API calls to aggregate spending data
        across all budgets, calculating totals and providing a comprehensive
        budget overview.

        Args:
                req: Request containing time period for analysis

        Returns:
                Comprehensive budget summary with totals

        """
        # Get all budgets
        budgets_array = await self._client.get_budgets()

        budget_spendings: list[BudgetSpending] = []
        total_spent = 0.0
        total_budgeted = 0.0

        for budget in budgets_array.data:
            spending_req = GetBudgetSpendingRequest(
                budget_id=budget.id,
                start_date=req.start_date,
                end_date=req.end_date,
            )
            budget_spending = await self.get_budget_spending(spending_req)
            budget_spendings.append(budget_spending)

            total_spent += budget_spending.spent
            if budget_spending.budgeted:
                total_budgeted += budget_spending.budgeted

        total_remaining = total_budgeted - total_spent if total_budgeted > 0 else None

        return BudgetSummary(
            budgets=budget_spendings,
            total_budgeted=total_budgeted if total_budgeted > 0 else None,
            total_spent=total_spent,
            total_remaining=total_remaining,
            available_budget=None,  # Would need additional API call to get available budget
        )

    async def get_available_budget(self, req: GetAvailableBudgetRequest) -> AvailableBudget:
        """Get available budget amount for a specified period.

        Args:
                req: Request containing time period for available budget

        Returns:
                Available budget information

        """
        available_array = await self._client.get_available_budgets(req.start_date, req.end_date)

        # Parse the available budget data
        if available_array.data:
            first_budget = available_array.data[0]
            attrs = first_budget.attributes
            today = date.today()
            return AvailableBudget(
                amount=float(attrs.amount) if attrs.amount is not None else 0.0,
                currency_code=attrs.currency_code or 'USD',
                start_date=req.start_date
                or (attrs.start.date() if attrs.start is not None else today.replace(day=1)),
                end_date=req.end_date or (attrs.end.date() if attrs.end is not None else today),
            )
        else:
            # Return default if no data available
            today = date.today()
            return AvailableBudget(
                amount=0.0,
                currency_code='USD',
                start_date=req.start_date or today.replace(day=1),
                end_date=req.end_date or today,
            )

    async def create_budget(self, req: CreateBudgetRequest) -> Budget:
        """Create a new budget.

        Args:
                req: Request containing budget creation parameters

        Returns:
                Created budget details

        """
        budget_store = BudgetStore(
            name=req.name,
            active=req.active,
            notes=req.notes,
        )

        # Handle auto-budget settings if provided
        if req.auto_budget_type is not None:
            budget_store.auto_budget_type = AutoBudgetType(AutoBudgetTypeEnum(req.auto_budget_type))

        if req.auto_budget_amount is not None:
            budget_store.auto_budget_amount = str(req.auto_budget_amount)

        if req.auto_budget_period is not None:
            budget_store.auto_budget_period = AutoBudgetPeriod(
                AutoBudgetPeriodEnum(req.auto_budget_period)
            )

        if req.auto_budget_currency_code is not None:
            budget_store.auto_budget_currency_code = req.auto_budget_currency_code

        budget_single = await self._client.create_budget(budget_store)
        return Budget.from_budget_read(budget_single.data)
