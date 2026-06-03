"""Budget Service for LamPyrid.

This service handles budget-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

from datetime import date, timedelta
from typing import List, Optional, Tuple

from ..clients.firefly import FireflyClient
from ..models.firefly_models import (
    AutoBudgetPeriod,
    AutoBudgetPeriodEnum,
    AutoBudgetType,
    AutoBudgetTypeEnum,
    BudgetLimitRead,
    BudgetLimitStore,
    BudgetLimitUpdate,
    BudgetStore,
)
from ..models.lampyrid_models import (
    AvailableBudget,
    Budget,
    BudgetLimit,
    BudgetSpending,
    BudgetSummary,
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

    async def _resolve_budget_id(self, budget_id: Optional[str], budget_name: Optional[str]) -> str:
        """Resolve a budget reference (ID or name) to a budget ID.

        If budget_id is provided it is returned as-is. Otherwise the budget is looked up
        by name (case-insensitive exact match) from the list of all budgets.

        Raises:
                ValueError: If no budget reference is given, the name is not found, or the
                        name matches more than one budget.

        """
        if budget_id is not None:
            return budget_id

        if budget_name is None:
            raise ValueError('Provide either budget_id or budget_name.')

        budgets_array = await self._client.get_budgets()
        matches = [
            budget
            for budget in budgets_array.data
            if budget.attributes.name.lower() == budget_name.lower()
        ]

        if not matches:
            raise ValueError(f'No budget found with name {budget_name!r}.')
        if len(matches) > 1:
            raise ValueError(
                f'Multiple budgets match name {budget_name!r}; use budget_id to disambiguate.'
            )
        return matches[0].id

    @staticmethod
    def _resolve_period(start_date: Optional[date], end_date: Optional[date]) -> Tuple[date, date]:
        """Resolve a period, defaulting to the current calendar month when omitted.

        Both dates must be provided together or neither. The request models already
        enforce this, but the helper validates it too in case it is called directly.
        """
        if (start_date is None) != (end_date is None):
            raise ValueError('Provide both start_date and end_date, or neither.')

        if start_date is not None and end_date is not None:
            return start_date, end_date

        today = date.today()
        first = today.replace(day=1)
        last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        return first, last

    async def _find_limit_for_period(
        self, budget_id: str, start: date, end: date
    ) -> Optional[BudgetLimitRead]:
        """Find an existing budget limit that exactly matches the given period."""
        limits_array = await self._client.get_budget_limits(budget_id, start, end)
        for limit in limits_array.data:
            attrs = limit.attributes
            if (
                attrs.start is not None
                and attrs.end is not None
                and attrs.start.date() == start
                and attrs.end.date() == end
            ):
                return limit
        return None

    async def set_budget_limit(self, req: SetBudgetLimitRequest) -> BudgetLimit:
        """Set (create or update) a budget limit for a budget and period.

        If a limit already exists for the exact period it is updated; otherwise a new
        limit is created. This makes the operation an idempotent upsert from the
        caller's perspective.

        Args:
                req: Request containing the budget reference, amount, and optional period.

        Returns:
                The created or updated budget limit.

        """
        budget_id = await self._resolve_budget_id(req.budget_id, req.budget_name)
        start, end = self._resolve_period(req.start_date, req.end_date)

        existing = await self._find_limit_for_period(budget_id, start, end)

        if existing is not None:
            limit_update = BudgetLimitUpdate(amount=str(req.amount))
            if req.notes is not None:
                limit_update.notes = req.notes
            limit_single = await self._client.update_budget_limit(
                budget_id, existing.id, limit_update
            )
        else:
            limit_store = BudgetLimitStore(
                budget_id=budget_id,
                start=start,
                end=end,
                amount=str(req.amount),
                currency_code=req.currency_code,
                notes=req.notes,
            )
            limit_single = await self._client.create_budget_limit(budget_id, limit_store)

        return BudgetLimit.from_budget_limit_read(limit_single.data)

    async def list_budget_limits(self, req: ListBudgetLimitsRequest) -> List[BudgetLimit]:
        """List budget limits for a budget, optionally filtered by date range.

        Args:
                req: Request containing the budget reference and optional date range.

        Returns:
                List of budget limits set for the budget.

        """
        budget_id = await self._resolve_budget_id(req.budget_id, req.budget_name)
        limits_array = await self._client.get_budget_limits(budget_id, req.start_date, req.end_date)
        return [BudgetLimit.from_budget_limit_read(limit) for limit in limits_array.data]

    async def delete_budget_limit(self, req: DeleteBudgetLimitRequest) -> bool:
        """Delete the budget limit for a budget and period.

        Args:
                req: Request containing the budget reference and optional period.

        Returns:
                True if the limit was deleted.

        Raises:
                ValueError: If no limit exists for the resolved period.

        """
        budget_id = await self._resolve_budget_id(req.budget_id, req.budget_name)
        start, end = self._resolve_period(req.start_date, req.end_date)

        existing = await self._find_limit_for_period(budget_id, start, end)
        if existing is None:
            raise ValueError(
                f'No budget limit set for budget {budget_id} for period '
                f'{start.isoformat()} to {end.isoformat()}.'
            )

        return await self._client.delete_budget_limit(budget_id, existing.id)
