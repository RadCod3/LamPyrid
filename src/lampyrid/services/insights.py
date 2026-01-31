"""Insight Service for LamPyrid.

This service handles insight-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

import asyncio

from ..clients.firefly import FireflyClient
from ..models.firefly_models import (
    InsightGroup,
    InsightTotal,
    InsightTransfer,
)
from ..models.lampyrid_models import (
    ExpenseInsightResult,
    FinancialSummary,
    GetExpenseInsightRequest,
    GetFinancialSummaryRequest,
    GetIncomeInsightRequest,
    GetTransferInsightRequest,
    IncomeInsightResult,
    InsightEntry,
    TransferInsightEntry,
    TransferInsightResult,
)


class InsightService:
    """Service for financial insight analysis.

    This service provides a high-level interface for insight operations,
    handling response transformation, grouping logic, and multi-call
    orchestration while delegating HTTP operations to the FireflyClient.
    """

    def __init__(self, client: FireflyClient) -> None:
        """Initialize the insight service with a FireflyClient instance."""
        self._client = client

    def _entries_from_insight_group(self, insight: InsightGroup) -> list[InsightEntry]:
        """Convert InsightGroup to list of InsightEntry."""
        entries = []
        for entry in insight.root:
            entries.append(
                InsightEntry(
                    id=entry.id,
                    name=entry.name,
                    amount=abs(entry.difference_float) if entry.difference_float else 0.0,
                    currency_code=entry.currency_code or 'USD',
                )
            )
        return entries

    def _entries_from_insight_total(
        self, insight: InsightTotal, name: str | None = None
    ) -> list[InsightEntry]:
        """Convert InsightTotal to list of InsightEntry."""
        entries = []
        for entry in insight.root:
            entries.append(
                InsightEntry(
                    id=None,
                    name=name,
                    amount=abs(entry.difference_float) if entry.difference_float else 0.0,
                    currency_code=entry.currency_code or 'USD',
                )
            )
        return entries

    def _entries_from_insight_transfer(
        self, insight: InsightTransfer
    ) -> list[TransferInsightEntry]:
        """Convert InsightTransfer to list of TransferInsightEntry."""
        entries = []
        for entry in insight.root:
            entries.append(
                TransferInsightEntry(
                    id=entry.id,
                    name=entry.name,
                    amount=abs(entry.difference_float) if entry.difference_float else 0.0,
                    amount_in=abs(entry.in_float) if entry.in_float else 0.0,
                    amount_out=abs(entry.out_float) if entry.out_float else 0.0,
                    currency_code=entry.currency_code or 'USD',
                )
            )
        return entries

    def _get_total_and_currency(
        self, entries: list[InsightEntry] | list[TransferInsightEntry]
    ) -> tuple[float, str]:
        """Calculate total amount and get primary currency from entries."""
        if not entries:
            return 0.0, 'USD'
        total = sum(e.amount for e in entries)
        currency = entries[0].currency_code if entries else 'USD'
        return total, currency

    async def get_expense_insight(self, req: GetExpenseInsightRequest) -> ExpenseInsightResult:
        """Get expense insights with optional grouping.

        Args:
            req: Request containing date range, grouping option, and filters

        Returns:
            Expense insight result with entries and totals

        """
        entries: list[InsightEntry] = []
        group_by = req.group_by

        if group_by == 'expense_account':
            insight = await self._client.get_expense_by_expense_account(
                req.start_date, req.end_date, req.account_ids
            )
            entries = self._entries_from_insight_group(insight)

        elif group_by == 'asset_account':
            insight = await self._client.get_expense_by_asset_account(
                req.start_date, req.end_date, req.account_ids
            )
            entries = self._entries_from_insight_group(insight)

        elif group_by == 'budget':
            # Get expenses by budget
            insight = await self._client.get_expense_by_budget(
                req.start_date, req.end_date, req.account_ids, req.budget_ids
            )
            entries = self._entries_from_insight_group(insight)

            # Optionally include unbudgeted expenses
            if req.include_unbudgeted:
                no_budget_insight = await self._client.get_expense_no_budget(
                    req.start_date, req.end_date, req.account_ids
                )
                unbudgeted_entries = self._entries_from_insight_total(
                    no_budget_insight, name='Unbudgeted'
                )
                entries.extend(unbudgeted_entries)

        else:
            # No grouping - return total only
            insight = await self._client.get_expense_total(
                req.start_date, req.end_date, req.account_ids
            )
            entries = self._entries_from_insight_total(insight, name='Total Expenses')

        total, currency = self._get_total_and_currency(entries)

        return ExpenseInsightResult(
            entries=entries,
            total_expenses=total,
            currency_code=currency,
            start_date=req.start_date,
            end_date=req.end_date,
            group_by=group_by,
        )

    async def get_income_insight(self, req: GetIncomeInsightRequest) -> IncomeInsightResult:
        """Get income insights with optional grouping.

        Args:
            req: Request containing date range, grouping option, and filters

        Returns:
            Income insight result with entries and totals

        """
        entries: list[InsightEntry] = []
        group_by = req.group_by

        if group_by == 'revenue_account':
            insight = await self._client.get_income_by_revenue_account(
                req.start_date, req.end_date, req.account_ids
            )
            entries = self._entries_from_insight_group(insight)

        elif group_by == 'asset_account':
            insight = await self._client.get_income_by_asset_account(
                req.start_date, req.end_date, req.account_ids
            )
            entries = self._entries_from_insight_group(insight)

        else:
            # No grouping - return total only
            insight = await self._client.get_income_total(
                req.start_date, req.end_date, req.account_ids
            )
            entries = self._entries_from_insight_total(insight, name='Total Income')

        total, currency = self._get_total_and_currency(entries)

        return IncomeInsightResult(
            entries=entries,
            total_income=total,
            currency_code=currency,
            start_date=req.start_date,
            end_date=req.end_date,
            group_by=group_by,
        )

    async def get_transfer_insight(self, req: GetTransferInsightRequest) -> TransferInsightResult:
        """Get transfer insights with optional grouping.

        Args:
            req: Request containing date range, grouping option, and filters

        Returns:
            Transfer insight result with entries and totals

        """
        entries: list[TransferInsightEntry] | list[InsightEntry] = []
        group_by = req.group_by

        if group_by == 'asset_account':
            insight = await self._client.get_transfer_by_asset_account(
                req.start_date, req.end_date, req.account_ids
            )
            entries = self._entries_from_insight_transfer(insight)
        else:
            # No grouping - return total only
            insight = await self._client.get_transfer_total(
                req.start_date, req.end_date, req.account_ids
            )
            entries = self._entries_from_insight_total(insight, name='Total Transfers')

        total, currency = self._get_total_and_currency(entries)

        return TransferInsightResult(
            entries=entries,
            total_transfers=total,
            currency_code=currency,
            start_date=req.start_date,
            end_date=req.end_date,
            group_by=group_by,
        )

    async def get_financial_summary(self, req: GetFinancialSummaryRequest) -> FinancialSummary:
        """Get complete financial summary with expense, income, and transfer totals.

        Makes parallel calls to all three total endpoints for efficiency.

        Args:
            req: Request containing date range and optional account filter

        Returns:
            Financial summary with totals and net position

        """
        # Make parallel calls to all total endpoints
        expense_task = self._client.get_expense_total(req.start_date, req.end_date, req.account_ids)
        income_task = self._client.get_income_total(req.start_date, req.end_date, req.account_ids)
        transfer_task = self._client.get_transfer_total(
            req.start_date, req.end_date, req.account_ids
        )

        expense_insight, income_insight, transfer_insight = await asyncio.gather(
            expense_task, income_task, transfer_task
        )

        # Extract totals (use first entry as primary, sum if multiple currencies)
        total_expenses = sum(
            abs(e.difference_float) if e.difference_float else 0.0 for e in expense_insight.root
        )
        total_income = sum(
            abs(e.difference_float) if e.difference_float else 0.0 for e in income_insight.root
        )
        total_transfers = sum(
            abs(e.difference_float) if e.difference_float else 0.0 for e in transfer_insight.root
        )

        # Get primary currency from income (most likely to have data)
        currency = 'USD'
        if income_insight.root:
            currency = income_insight.root[0].currency_code or 'USD'
        elif expense_insight.root:
            currency = expense_insight.root[0].currency_code or 'USD'

        net_position = total_income - total_expenses

        return FinancialSummary(
            total_expenses=total_expenses,
            total_income=total_income,
            total_transfers=total_transfers,
            net_position=net_position,
            currency_code=currency,
            start_date=req.start_date,
            end_date=req.end_date,
        )
