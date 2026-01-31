"""Simplified models for MCP tool interfaces with budget support."""

from datetime import date, datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .firefly_models import (
    AccountRead,
    AccountTypeFilter,
    BudgetRead,
    ShortAccountTypeProperty,
    TransactionArray,
    TransactionRead,
    TransactionSingle,
    TransactionSplitStore,
    TransactionTypeFilter,
    TransactionTypeProperty,
)


def utc_now():
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class Account(BaseModel):
    """Simplified account model for MCP responses."""

    id: str = Field(..., description='Unique identifier for the account', examples=['2'])
    name: str = Field(..., description='Display name of the account', examples=['Cash'])
    type: ShortAccountTypeProperty = Field(
        ..., description='Type of the account', examples=['asset']
    )
    currency_code: Optional[str] = Field(
        None, description='Currency code (ISO 4217) for the account', examples=['GBP']
    )
    current_balance: Optional[float] = Field(
        None, description='Current account balance as a decimal number', examples=[1000.0]
    )

    @classmethod
    def from_account_read(cls, account_read: 'AccountRead') -> 'Account':
        """Create an Account instance from a Firefly AccountRead object."""
        return cls(
            id=account_read.id,
            name=account_read.attributes.name,
            type=account_read.attributes.type,
            currency_code=account_read.attributes.currency_code,
            current_balance=(
                float(account_read.attributes.current_balance)
                if account_read.attributes.current_balance
                else None
            ),
        )


class Budget(BaseModel):
    """Simplified budget model for MCP responses."""

    id: str = Field(..., description='Unique identifier for the budget', examples=['2'])
    name: str = Field(..., description='Display name of the budget', examples=['Groceries'])
    active: Optional[bool] = Field(
        None,
        description='Whether this budget is currently active for new transactions',
        examples=[True],
    )
    notes: Optional[str] = Field(
        None,
        description='Optional notes or description about this budget',
        examples=['Monthly grocery budget'],
    )
    order: Optional[int] = Field(
        None, description='Display order for sorting budgets', examples=[1]
    )

    @classmethod
    def from_budget_read(cls, budget_read: 'BudgetRead') -> 'Budget':
        """Create a Budget instance from a Firefly BudgetRead object."""
        return cls(
            id=budget_read.id,
            name=budget_read.attributes.name,
            active=budget_read.attributes.active,
            notes=budget_read.attributes.notes,
            order=budget_read.attributes.order,
        )


class Transaction(BaseModel):
    """Simplified transaction model for MCP responses."""

    id: Optional[str] = Field(None, description='Transaction ID')
    amount: float = Field(..., description='Amount of the transaction')
    description: str = Field(..., description='Description of the transaction')
    type: TransactionTypeProperty = Field(..., description='Type of the transaction')
    date: datetime = Field(default_factory=utc_now, description='Date and time of the transaction')
    source_id: Optional[str] = Field(
        None,
        description=(
            'ID of the source account. For withdrawal/transfer, must be asset account. '
            'For deposits, must be revenue account.'
        ),
    )
    destination_id: Optional[str] = Field(
        None,
        description=(
            'ID of the destination account. For deposit/transfer, must be asset account. '
            'For withdrawals, must be expense account.'
        ),
    )
    source_name: Optional[str] = Field(None, description='Source account name')
    destination_name: Optional[str] = Field(None, description='Destination account name')
    currency_code: Optional[str] = Field(None, description='Currency code')
    budget_id: Optional[str] = Field(None, description='ID of the budget for this transaction')
    budget_name: Optional[str] = Field(None, description='Name of the budget for this transaction')

    @classmethod
    def from_transaction_single(cls, trx: TransactionSingle) -> 'Transaction':
        """Create a Transaction instance from a Firefly III TransactionSingle response."""
        inner_trx = trx.data.attributes.transactions[0]
        return cls(
            id=trx.data.id,
            amount=float(inner_trx.amount),
            description=inner_trx.description,
            type=inner_trx.type,
            date=inner_trx.date,
            source_id=inner_trx.source_id,
            destination_id=inner_trx.destination_id,
            source_name=inner_trx.source_name,
            destination_name=inner_trx.destination_name,
            currency_code=inner_trx.currency_code,
            budget_id=inner_trx.budget_id,
            budget_name=inner_trx.budget_name,
        )

    @classmethod
    def from_transaction_read(cls, transaction_read: TransactionRead) -> 'Transaction':
        """Create a Transaction from a Firefly TransactionRead object."""
        first_trx = transaction_read.attributes.transactions[0]
        return cls(
            id=transaction_read.id,
            description=first_trx.description,
            amount=float(first_trx.amount),
            date=first_trx.date,
            type=first_trx.type,
            source_id=first_trx.source_id,
            destination_id=first_trx.destination_id,
            source_name=first_trx.source_name,
            destination_name=first_trx.destination_name,
            currency_code=first_trx.currency_code,
            budget_id=first_trx.budget_id,
            budget_name=first_trx.budget_name,
        )

    def to_transaction_split_store(self) -> TransactionSplitStore:
        """Convert this transaction to a Firefly III TransactionSplitStore for API requests."""
        return TransactionSplitStore(
            type=self.type,
            date=self.date,
            amount=str(self.amount),
            description=self.description,
            source_id=self.source_id,
            destination_id=self.destination_id,
            source_name=self.source_name,
            destination_name=self.destination_name,
            budget_id=self.budget_id,
            budget_name=self.budget_name,
        )


class ListAccountRequest(BaseModel):
    """Request model for listing accounts."""

    model_config = ConfigDict(extra='forbid')

    type: AccountTypeFilter = Field(
        ...,
        description=(
            'Account type: asset (your accounts), expense (spending categories), '
            'revenue (income sources), liability (debts), or all'
        ),
    )


class SearchAccountRequest(BaseModel):
    """Request model for searching accounts."""

    model_config = ConfigDict(extra='forbid')

    query: str = Field(
        ...,
        description='Text to search for in account names (supports partial matching)',
        min_length=1,
    )
    type: AccountTypeFilter = Field(
        AccountTypeFilter.all,
        description=(
            'Limit search to specific account type (asset, expense, revenue, liability, or all)'
        ),
    )


class GetAccountRequest(BaseModel):
    """Request model for getting a single account."""

    model_config = ConfigDict(extra='forbid')

    id: str = Field(
        ..., description='Unique identifier of the account (from list_accounts or search_accounts)'
    )


class CreateWithdrawalRequest(BaseModel):
    """Request model for creating a withdrawal transaction."""

    model_config = ConfigDict(extra='forbid')

    amount: float = Field(
        ..., description='Amount to withdraw as positive number (e.g., 25.50 for $25.50 expense)'
    )
    description: str = Field(
        ..., description='What this expense was for (e.g., "Grocery shopping at Whole Foods")'
    )
    date: datetime = Field(
        default_factory=utc_now,
        description='When the expense occurred (defaults to current time if not specified)',
    )
    source_id: str = Field(
        ...,
        description=(
            'ID of your account the money comes from (checking, savings, cash, etc.). '
            'Must be an asset account you own.'
        ),
    )
    destination_id: Optional[str] = Field(
        default=None,
        description=(
            'ID of the expense account receiving the money (from list_accounts type=expense). '
            'Use destination_id OR destination_name, not both. '
            'If neither provided, defaults to Cash.'
        ),
    )
    destination_name: Optional[str] = Field(
        default=None,
        description=(
            'Where the money went ("Groceries", "Gas Station", "ATM"). '
            'Creates expense account if new. Use destination_id OR destination_name, not both. '
            'If neither provided, defaults to Cash.'
        ),
    )
    budget_id: Optional[str] = Field(
        None, description='Budget to track this expense against (from list_budgets)'
    )
    budget_name: Optional[str] = Field(
        None,
        description='Name of budget if ID is unknown. Will use ID if both provided.',
    )

    @model_validator(mode='after')
    def validate_destination_mutual_exclusivity(self):
        """Ensure destination_id and destination_name are not both provided."""
        if self.destination_id is not None and self.destination_name is not None:
            raise ValueError(
                'Cannot specify both destination_id and destination_name. Use one or the other.'
            )
        return self


class CreateDepositRequest(BaseModel):
    """Request model for creating a deposit transaction."""

    model_config = ConfigDict(extra='forbid')

    amount: float = Field(
        ..., description='Amount received as positive number (e.g., 2500.00 for $2500 salary)'
    )
    description: str = Field(
        ..., description='What this income was for (e.g., "Monthly salary", "Freelance payment")'
    )
    date: datetime = Field(
        default_factory=utc_now,
        description='When the income was received (defaults to current time if not specified)',
    )
    source_id: Optional[str] = Field(
        default=None,
        description=(
            'ID of the revenue account the money comes from (from list_accounts type=revenue). '
            'Use source_id OR source_name, not both. '
            'If neither provided, defaults to Cash.'
        ),
    )
    source_name: Optional[str] = Field(
        default=None,
        description=(
            'Where the money came from ("Employer", "Client Name", "Gift"). '
            'Creates revenue account if new. Use source_id OR source_name, not both. '
            'If neither provided, defaults to Cash.'
        ),
    )
    destination_id: str = Field(
        ...,
        description=(
            'ID of your account receiving the money (checking, savings, etc.). '
            'Must be an asset account you own.'
        ),
    )

    @model_validator(mode='after')
    def validate_source_mutual_exclusivity(self):
        """Ensure source_id and source_name are not both provided."""
        if self.source_id is not None and self.source_name is not None:
            raise ValueError('Cannot specify both source_id and source_name. Use one or the other.')
        return self


class CreateTransferRequest(BaseModel):
    """Request model for creating a transfer transaction."""

    model_config = ConfigDict(extra='forbid')

    amount: float = Field(
        ..., description='Amount to move as positive number (e.g., 500.00 to move $500)'
    )
    description: str = Field(
        ...,
        description='Purpose of the transfer (e.g., "Transfer to savings", "Credit card payment")',
    )
    date: datetime = Field(
        default_factory=utc_now,
        description='When the transfer occurred (defaults to current time if not specified)',
    )
    source_id: str = Field(
        ...,
        description='ID of your account the money comes from. Must be an asset account you own.',
    )
    destination_id: str = Field(
        ...,
        description='ID of your account receiving the money. Must be an asset account you own.',
    )


class GetTransactionsRequest(BaseModel):
    """Request model for retrieving transactions."""

    model_config = ConfigDict(extra='forbid')

    account_id: Optional[str] = Field(
        None,
        description=(
            'Optional account ID to filter results. When provided, only transactions '
            'involving this specific account (as source or destination) are returned. '
            'When omitted or None, transactions for all accounts are returned.'
        ),
    )
    start_date: Optional[date] = Field(
        None,
        description='Start date for filtering transactions (YYYY-MM-DD). '
        'If not specified, returns recent transactions.',
    )
    end_date: Optional[date] = Field(
        None,
        description='End date for filtering transactions (YYYY-MM-DD). '
        'If not specified, returns up to current date.',
    )
    transaction_type: Optional[TransactionTypeFilter] = Field(
        None,
        description='Filter by transaction type: withdrawal (expenses), deposit (income), '
        'transfer (accounts)',
    )
    page: Optional[int] = Field(
        1,
        description='Page number to retrieve (1-based). Use for browsing large result sets.',
        ge=1,
    )
    limit: Optional[int] = Field(
        50, description='Maximum number of transactions to return per page (1-500)', ge=1, le=500
    )


class SearchTransactionsRequest(BaseModel):
    """Request model for searching transactions."""

    model_config = ConfigDict(extra='forbid')

    query: str | None = Field(
        None,
        description=(
            'Free-text search or raw Firefly III query string. '
            'Can be combined with structured filters below.'
        ),
    )

    # Transaction type and amount filters
    type: Literal['withdrawal', 'deposit', 'transfer'] | None = Field(
        None,
        description='Transaction type to filter by',
        examples=['withdrawal', 'deposit', 'transfer'],
    )
    amount_equals: float | None = Field(
        None,
        description='Exact amount to match',
        examples=[123.45],
    )
    amount_more: float | None = Field(
        None,
        description='Minimum amount (inclusive)',
        examples=[100.00],
    )
    amount_less: float | None = Field(
        None,
        description='Maximum amount (inclusive)',
        examples=[50.00],
    )

    # Date filters
    date_on: date | None = Field(
        None,
        description='Exact date match in YYYY-MM-DD format',
        examples=['2024-01-15'],
    )
    date_after: date | None = Field(
        None,
        description='From date (inclusive) in YYYY-MM-DD format',
        examples=['2024-01-01'],
    )
    date_before: date | None = Field(
        None,
        description='Until date (inclusive) in YYYY-MM-DD format',
        examples=['2024-12-31'],
    )

    # Content filters
    description_contains: str | None = Field(
        None,
        description='Text to search for in transaction descriptions',
        examples=['groceries', 'coffee'],
    )

    # Metadata filters
    category: str | None = Field(
        None,
        description='Category name to filter by (exact match)',
        examples=['Food', 'Transportation'],
    )
    budget: str | None = Field(
        None,
        description='Budget name to filter by (exact match)',
        examples=['Groceries', 'Dining Out'],
    )

    # Account filters
    account_contains: str | None = Field(
        None,
        description='Text to search for in any account name (source or destination)',
        examples=['checking', 'savings'],
    )
    account_id: str | None = Field(
        None,
        description='Account ID to filter by (matches source or destination account)',
        examples=['123'],
    )

    # Pagination
    page: int | None = Field(
        1,
        description='Page number to retrieve (1-based). Use for browsing large result sets.',
        ge=1,
    )
    limit: int | None = Field(
        50, description='Maximum number of transactions to return per page (1-500)', ge=1, le=500
    )

    @model_validator(mode='after')
    def validate_search_criteria(self):
        """Ensure at least one search criterion is provided."""
        search_fields = [
            self.query,
            self.type,
            self.amount_equals,
            self.amount_more,
            self.amount_less,
            self.date_on,
            self.date_after,
            self.date_before,
            self.description_contains,
            self.category,
            self.budget,
            self.account_contains,
            self.account_id,
        ]
        # Consider a field provided if: (a) it's not None and not a string, or
        # (b) it's a string and not empty/whitespace-only
        has_criteria = any(
            (field is not None and not isinstance(field, str))
            or (isinstance(field, str) and field.strip() != '')
            for field in search_fields
        )
        if not has_criteria:
            raise ValueError('At least one search criterion must be provided')
        return self


class DeleteTransactionRequest(BaseModel):
    """Request model for deleting a transaction."""

    model_config = ConfigDict(extra='forbid')

    id: str = Field(..., description='Unique identifier of the transaction to permanently remove')


class GetTransactionRequest(BaseModel):
    """Request model for getting a single transaction."""

    model_config = ConfigDict(extra='forbid')

    id: str = Field(..., description='Unique identifier of the transaction to get details for')


class BulkOperationError(BaseModel):
    """Error details for a failed operation in a bulk request."""

    index: int = Field(..., description='Zero-based index of the failed item in the request')
    transaction_id: Optional[str] = Field(
        None, description='Transaction ID if available (for updates)'
    )
    error: str = Field(..., description='Error message describing what went wrong')


class BulkCreateResult(BaseModel):
    """Result of a bulk transaction creation operation."""

    successful: List[Transaction] = Field(
        default_factory=list, description='Transactions that were successfully created'
    )
    failed: List[BulkOperationError] = Field(
        default_factory=list, description='Errors for transactions that failed to create'
    )
    total_requested: int = Field(..., description='Total number of transactions requested')
    total_succeeded: int = Field(..., description='Number of transactions successfully created')
    total_failed: int = Field(..., description='Number of transactions that failed')


class BulkUpdateResult(BaseModel):
    """Result of a bulk transaction update operation."""

    successful: List[Transaction] = Field(
        default_factory=list, description='Transactions that were successfully updated'
    )
    failed: List[BulkOperationError] = Field(
        default_factory=list, description='Errors for transactions that failed to update'
    )
    total_requested: int = Field(..., description='Total number of updates requested')
    total_succeeded: int = Field(..., description='Number of transactions successfully updated')
    total_failed: int = Field(..., description='Number of updates that failed')


class TransactionListResponse(BaseModel):
    """Response model for transaction listings."""

    transactions: List[Transaction] = Field(
        ..., description='Array of transaction objects matching the request'
    )
    total_count: Optional[int] = Field(
        None,
        description=(
            'Total transactions available across all pages (if pagination metadata available)'
        ),
    )
    current_page: int = Field(..., description='Current page number in the result set')
    per_page: int = Field(..., description='Number of transactions included in this page')

    @classmethod
    def from_transaction_array(
        cls, transaction_array: TransactionArray, current_page: int, per_page: int
    ) -> 'TransactionListResponse':
        """Create a TransactionListResponse from a Firefly TransactionArray."""
        transactions = [
            Transaction.from_transaction_read(trx_read) for trx_read in transaction_array.data
        ]
        return cls(
            transactions=transactions,
            total_count=transaction_array.meta.pagination.total
            if transaction_array.meta.pagination
            else None,
            current_page=current_page,
            per_page=per_page,
        )


class ListBudgetsRequest(BaseModel):
    """Request for listing budgets."""

    model_config = ConfigDict(extra='forbid')

    active: Optional[bool] = Field(
        None,
        description='Show only active budgets (true), inactive (false), or all budgets '
        '(not specified)',
    )


class GetBudgetRequest(BaseModel):
    """Request for getting a single budget by ID."""

    model_config = ConfigDict(extra='forbid')

    id: str = Field(..., description='Unique identifier of the budget to get details for')


class BudgetSpending(BaseModel):
    """Budget spending information for a specific period."""

    budget_id: str = Field(..., description='Unique identifier of the budget')
    budget_name: str = Field(..., description='Display name of the budget')
    spent: float = Field(
        ..., description='Total amount spent from this budget in the specified period'
    )
    budgeted: Optional[float] = Field(
        None, description='Amount allocated to this budget for the period'
    )
    remaining: Optional[float] = Field(
        None, description='Money left in this budget (budgeted minus spent)'
    )
    percentage_spent: Optional[float] = Field(
        None,
        description='Percentage of allocated budget used (0-100+, can exceed 100 if overspent)',
    )


class GetBudgetSpendingRequest(BaseModel):
    """Request for getting budget spending data."""

    model_config = ConfigDict(extra='forbid')

    budget_id: str = Field(
        ..., description='Unique identifier of the budget to analyze spending for'
    )
    start_date: Optional[date] = Field(
        None, description='Start date for spending period (YYYY-MM-DD), inclusive'
    )
    end_date: Optional[date] = Field(
        None, description='End date for spending period (YYYY-MM-DD), inclusive'
    )


class BudgetSummary(BaseModel):
    """Summary of all budgets with spending information."""

    budgets: List[BudgetSpending] = Field(..., description='Spending analysis for each budget')
    total_budgeted: Optional[float] = Field(None, description='Sum of all allocated budget amounts')
    total_spent: float = Field(..., description='Sum of all spending across budgets')
    total_remaining: Optional[float] = Field(
        None, description='Total money left across all budgets'
    )
    available_budget: Optional[float] = Field(
        None,
        description='Unallocated money available for new budgets or unexpected expenses',
    )


class GetBudgetSummaryRequest(BaseModel):
    """Request for getting budget summary."""

    model_config = ConfigDict(extra='forbid')

    start_date: Optional[date] = Field(
        None, description='Start date for summary period (YYYY-MM-DD), inclusive'
    )
    end_date: Optional[date] = Field(
        None, description='End date for summary period (YYYY-MM-DD), inclusive'
    )


class AvailableBudget(BaseModel):
    """Available budget information for a period."""

    amount: float = Field(..., description='Total unallocated budget available for the period')
    currency_code: str = Field(..., description='Currency code (ISO 4217) for the budget amount')
    start_date: date = Field(..., description='Beginning of the budget period this amount covers')
    end_date: date = Field(..., description='End of the budget period this amount covers')


class GetAvailableBudgetRequest(BaseModel):
    """Request for getting available budget."""

    model_config = ConfigDict(extra='forbid')

    start_date: Optional[date] = Field(
        None,
        description='Start date for budget analysis (YYYY-MM-DD). Defaults to '
        'beginning of current month.',
    )
    end_date: Optional[date] = Field(
        None,
        description=(
            'End date for budget analysis (YYYY-MM-DD format). Defaults to end of current month.'
        ),
    )


class CreateBudgetRequest(BaseModel):
    """Request model for creating a new budget."""

    model_config = ConfigDict(extra='forbid')

    name: str = Field(
        ...,
        description='Name of the budget (e.g., "Groceries", "Entertainment")',
        min_length=1,
    )
    auto_budget_type: Optional[Literal['none', 'reset', 'rollover']] = Field(
        None,
        description=(
            'Auto-budget behavior: none (manual), reset (fixed amount each period), '
            'rollover (unused balance carries forward)'
        ),
    )
    auto_budget_amount: Optional[float] = Field(
        None,
        description='Amount to auto-allocate each period (required if auto_budget_type is set)',
        gt=0,
    )
    auto_budget_period: Optional[
        Literal['daily', 'weekly', 'monthly', 'quarterly', 'half-year', 'yearly']
    ] = Field(
        None,
        description='How often to reset/add to the budget (required if auto_budget_type is set)',
    )
    auto_budget_currency_code: Optional[str] = Field(
        None,
        description='Currency code for auto-budget amount (ISO 4217, e.g., "USD", "EUR")',
    )
    active: bool = Field(
        True,
        description='Whether the budget is active for new transactions',
    )
    notes: Optional[str] = Field(
        None,
        description='Optional notes or description about this budget',
    )

    @model_validator(mode='after')
    def validate_auto_budget(self) -> 'CreateBudgetRequest':
        """Ensure auto-budget fields are provided when auto_budget_type is set."""
        if self.auto_budget_type and self.auto_budget_type != 'none':
            if self.auto_budget_amount is None:
                raise ValueError('auto_budget_amount is required when auto_budget_type is set')
            if self.auto_budget_period is None:
                raise ValueError('auto_budget_period is required when auto_budget_type is set')
        return self


class CreateBulkTransactionsRequest(BaseModel):
    """Create multiple transactions in one operation."""

    model_config = ConfigDict(extra='forbid')

    transactions: List[Transaction] = Field(
        ...,
        description=(
            'List of transactions to create (can be mixed types: withdrawals, deposits, transfers)'
        ),
        min_length=1,
        max_length=100,
    )
    atomic: bool = Field(
        default=True,
        description=(
            'If True (default), all transactions are rolled back if any creation fails. '
            'If False, continues on error and returns partial results.'
        ),
    )

    @model_validator(mode='after')
    def validate_transactions(self):
        """Ensure transactions are only of allowed types."""
        for trx in self.transactions:
            if trx.type not in {
                TransactionTypeProperty.withdrawal,
                TransactionTypeProperty.deposit,
                TransactionTypeProperty.transfer,
            }:
                raise ValueError(
                    f'Invalid transaction type: {trx.type}. '
                    f'Only withdrawal, deposit, and transfer are allowed.'
                )
        return self


class UpdateTransactionRequest(BaseModel):
    """Update an existing transaction."""

    model_config = ConfigDict(extra='forbid')

    transaction_id: str = Field(..., description='Unique identifier of the transaction to modify')
    amount: Optional[float] = Field(None, description='New transaction amount (positive number)')
    description: Optional[str] = Field(
        None, description='New description for what the transaction was for'
    )
    date: Optional[datetime] = Field(
        None, description='New date/time when the transaction occurred'
    )
    source_id: Optional[str] = Field(
        None, description='New source account ID (where money comes from)'
    )
    destination_id: Optional[str] = Field(
        None, description='New destination account ID (where money goes to)'
    )
    budget_id: Optional[str] = Field(
        None, description='New budget ID to assign, or None to remove budget assignment'
    )
    category_name: Optional[str] = Field(
        None, description='New category name for transaction classification'
    )


class BulkUpdateTransactionsRequest(BaseModel):
    """Update multiple transactions in one operation."""

    model_config = ConfigDict(extra='forbid')

    updates: List[UpdateTransactionRequest] = Field(
        ...,
        description='Array of transaction modifications to apply in a single operation',
        min_length=1,
        max_length=50,
    )


# =============================================================================
# Insight Models - Request and Response models for financial insights
# =============================================================================


class GetExpenseInsightRequest(BaseModel):
    """Request for expense insight analysis."""

    model_config = ConfigDict(extra='forbid')

    start_date: date = Field(..., description='Start date for the analysis period (YYYY-MM-DD)')
    end_date: date = Field(..., description='End date for the analysis period (YYYY-MM-DD)')
    group_by: Optional[Literal['expense_account', 'asset_account', 'budget']] = Field(
        None,
        description=(
            'How to group expenses: expense_account (by vendor/payee), '
            'asset_account (by source account), budget (by budget category). '
            'If not specified, returns total only.'
        ),
    )
    account_ids: Optional[List[int]] = Field(
        None,
        description=(
            'Filter to specific account IDs. For expense_account grouping, these are expense '
            'accounts. For asset_account grouping, these are asset accounts.'
        ),
    )
    budget_ids: Optional[List[int]] = Field(
        None,
        description='Filter to specific budget IDs. Only used when group_by is "budget".',
    )
    include_unbudgeted: bool = Field(
        True,
        description=(
            'When group_by is "budget", include expenses not assigned to any budget '
            'as a separate entry.'
        ),
    )


class GetIncomeInsightRequest(BaseModel):
    """Request for income insight analysis."""

    model_config = ConfigDict(extra='forbid')

    start_date: date = Field(..., description='Start date for the analysis period (YYYY-MM-DD)')
    end_date: date = Field(..., description='End date for the analysis period (YYYY-MM-DD)')
    group_by: Optional[Literal['revenue_account', 'asset_account']] = Field(
        None,
        description=(
            'How to group income: revenue_account (by income source), '
            'asset_account (by receiving account). '
            'If not specified, returns total only.'
        ),
    )
    account_ids: Optional[List[int]] = Field(
        None,
        description='Filter to specific account IDs.',
    )


class GetTransferInsightRequest(BaseModel):
    """Request for transfer insight analysis."""

    model_config = ConfigDict(extra='forbid')

    start_date: date = Field(..., description='Start date for the analysis period (YYYY-MM-DD)')
    end_date: date = Field(..., description='End date for the analysis period (YYYY-MM-DD)')
    group_by: Optional[Literal['asset_account']] = Field(
        None,
        description=(
            'Group transfers by asset_account to see in/out breakdown per account. '
            'If not specified, returns total only.'
        ),
    )
    account_ids: Optional[List[int]] = Field(
        None,
        description='Filter to specific asset account IDs.',
    )


class GetFinancialSummaryRequest(BaseModel):
    """Request for complete financial summary."""

    model_config = ConfigDict(extra='forbid')

    start_date: date = Field(..., description='Start date for the analysis period (YYYY-MM-DD)')
    end_date: date = Field(..., description='End date for the analysis period (YYYY-MM-DD)')
    account_ids: Optional[List[int]] = Field(
        None,
        description='Filter to specific account IDs for all calculations.',
    )


class InsightEntry(BaseModel):
    """Single insight data point representing grouped financial data."""

    id: Optional[str] = Field(
        None,
        description='Reference ID of the grouped entity (account ID, budget ID, etc.)',
    )
    name: Optional[str] = Field(
        None,
        description='Display name of the grouped entity',
    )
    amount: float = Field(
        ...,
        description='Total amount for this entry (negative for expenses, positive for income)',
    )
    currency_code: str = Field(
        ...,
        description='Currency code (ISO 4217) for the amount',
    )


class TransferInsightEntry(InsightEntry):
    """Transfer-specific insight with in/out breakdown per account."""

    amount_in: float = Field(
        ...,
        description='Total amount transferred INTO this account',
    )
    amount_out: float = Field(
        ...,
        description='Total amount transferred OUT OF this account',
    )


class ExpenseInsightResult(BaseModel):
    """Result of expense insight analysis."""

    entries: List[InsightEntry] = Field(
        ...,
        description='List of expense entries, grouped as requested',
    )
    total_expenses: float = Field(
        ...,
        description='Total expenses for the period (as positive number)',
    )
    currency_code: str = Field(
        ...,
        description='Primary currency code for the totals',
    )
    start_date: date = Field(..., description='Start of the analysis period')
    end_date: date = Field(..., description='End of the analysis period')
    group_by: Optional[str] = Field(
        None,
        description='The grouping method used, if any',
    )


class IncomeInsightResult(BaseModel):
    """Result of income insight analysis."""

    entries: List[InsightEntry] = Field(
        ...,
        description='List of income entries, grouped as requested',
    )
    total_income: float = Field(
        ...,
        description='Total income for the period (as positive number)',
    )
    currency_code: str = Field(
        ...,
        description='Primary currency code for the totals',
    )
    start_date: date = Field(..., description='Start of the analysis period')
    end_date: date = Field(..., description='End of the analysis period')
    group_by: Optional[str] = Field(
        None,
        description='The grouping method used, if any',
    )


class TransferInsightResult(BaseModel):
    """Result of transfer insight analysis."""

    entries: list[TransferInsightEntry] | list[InsightEntry] = Field(
        ...,
        description='List of transfer entries. When grouped by account, includes in/out breakdown.',
    )
    total_transfers: float = Field(
        ...,
        description='Total transfer amount for the period',
    )
    currency_code: str = Field(
        ...,
        description='Primary currency code for the totals',
    )
    start_date: date = Field(..., description='Start of the analysis period')
    end_date: date = Field(..., description='End of the analysis period')
    group_by: Optional[str] = Field(
        None,
        description='The grouping method used, if any',
    )


class FinancialSummary(BaseModel):
    """Complete financial summary with expense, income, and transfer totals."""

    total_expenses: float = Field(
        ...,
        description='Total expenses for the period (as positive number)',
    )
    total_income: float = Field(
        ...,
        description='Total income for the period (as positive number)',
    )
    total_transfers: float = Field(
        ...,
        description='Total transfer amount for the period',
    )
    net_position: float = Field(
        ...,
        description='Net financial position (income - expenses). Positive means net gain.',
    )
    currency_code: str = Field(
        ...,
        description='Primary currency code for all amounts',
    )
    start_date: date = Field(..., description='Start of the analysis period')
    end_date: date = Field(..., description='End of the analysis period')
