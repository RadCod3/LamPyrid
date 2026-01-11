from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, model_validator

from .firefly_models import (
	AccountRead,
	AccountTypeFilter,
	BudgetRead,
	TransactionArray,
	TransactionRead,
	TransactionSingle,
	TransactionSplitStore,
	TransactionTypeFilter,
	TransactionTypeProperty,
)


def utc_now():
	"""Return current UTC time with timezone info"""
	return datetime.now(timezone.utc)


class Account(BaseModel):
	id: str = Field(..., description='Unique identifier for the account', examples=['2'])
	name: str = Field(..., description='Display name of the account', examples=['Cash'])
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
			currency_code=account_read.attributes.currency_code,
			current_balance=(
				float(account_read.attributes.current_balance)
				if account_read.attributes.current_balance
				else None
			),
		)


class Budget(BaseModel):
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


class TransactionType(Enum):
	withdrawal = 'withdrawal'
	deposit = 'deposit'
	transfer = 'transfer'


class Transaction(BaseModel):
	id: Optional[str] = Field(None, description='Transaction ID')
	amount: float = Field(..., description='Amount of the transaction')
	description: str = Field(..., description='Description of the transaction')
	type: TransactionType = Field(..., description='Type of the transaction')
	date: datetime = Field(
		default_factory=datetime.now, description='Date and time of the transaction'
	)
	source_id: Optional[str] = Field(
		None,
		description='ID of the source account. For a withdrawal or a transfer, this must always be an asset account. For deposits, this must be a revenue account.',
	)
	destination_id: Optional[str] = Field(
		None,
		description='ID of the destination account. For a deposit or a transfer, this must always be an asset account. For withdrawals this must be an expense account.',
	)
	source_name: Optional[str] = Field(None, description='Source account name')
	destination_name: Optional[str] = Field(None, description='Destination account name')
	currency_code: Optional[str] = Field(None, description='Currency code')
	budget_id: Optional[str] = Field(None, description='ID of the budget for this transaction')
	budget_name: Optional[str] = Field(None, description='Name of the budget for this transaction')

	@classmethod
	def from_transaction_single(cls, trx: TransactionSingle) -> 'Transaction':
		inner_trx = trx.data.attributes.transactions[0]
		return cls(
			id=trx.data.id,
			amount=float(inner_trx.amount),
			description=inner_trx.description,
			type=TransactionType[inner_trx.type.value],
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
			type=TransactionType[first_trx.type.value]
			if first_trx.type
			else TransactionType.withdrawal,
			source_id=first_trx.source_id,
			destination_id=first_trx.destination_id,
			source_name=first_trx.source_name,
			destination_name=first_trx.destination_name,
			currency_code=first_trx.currency_code,
			budget_id=first_trx.budget_id,
			budget_name=first_trx.budget_name,
		)

	def to_transaction_split_store(self) -> TransactionSplitStore:
		return TransactionSplitStore(
			type=TransactionTypeProperty(self.type.value),
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
	type: AccountTypeFilter = Field(
		...,
		description='Account type: asset (your accounts), expense (spending categories), revenue (income sources), liability (debts), or all',
	)


class SearchAccountRequest(BaseModel):
	query: str = Field(
		..., description='Text to search for in account names (supports partial matching)'
	)
	type: AccountTypeFilter = Field(
		AccountTypeFilter.all,
		description='Limit search to specific account type (asset, expense, revenue, liability, or all)',
	)


class GetAccountRequest(BaseModel):
	id: str = Field(
		..., description='Unique identifier of the account (from list_accounts or search_accounts)'
	)


class CreateWithdrawalRequest(BaseModel):
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
		description='ID of your account the money comes from (checking, savings, cash, etc.). Must be an asset account you own.',
	)
	destination_name: Optional[str] = Field(
		default=None,
		description='Where the money went ("Groceries", "Gas Station", "ATM"). Creates expense account if new. Leave blank for cash withdrawals.',
	)
	budget_id: Optional[str] = Field(
		None, description='Budget to track this expense against (from list_budgets)'
	)
	budget_name: Optional[str] = Field(
		None,
		description='Name of budget if ID is unknown. Will use ID if both provided.',
	)


class CreateDepositRequest(BaseModel):
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
	source_name: Optional[str] = Field(
		default=None,
		description='Where the money came from ("Employer", "Client Name", "Gift"). Creates revenue account if new.',
	)
	destination_id: str = Field(
		...,
		description='ID of your account receiving the money (checking, savings, etc.). Must be an asset account you own.',
	)


class CreateTransferRequest(BaseModel):
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
	account_id: Optional[str] = Field(
		None,
		description='Optional account ID to filter results. When provided, only transactions involving this '
		'specific account (as source or destination) are returned. When omitted or None, '
		'transactions for all accounts are returned (subject to other filters).',
	)
	start_date: Optional[date] = Field(
		None,
		description='Start date for filtering transactions (YYYY-MM-DD format). If not specified, returns recent transactions.',
	)
	end_date: Optional[date] = Field(
		None,
		description='End date for filtering transactions (YYYY-MM-DD format). If not specified, returns up to current date.',
	)
	transaction_type: Optional[TransactionTypeFilter] = Field(
		None,
		description='Filter by transaction type: withdrawal (expenses), deposit (income), or transfer (between accounts)',
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
	query: str | None = Field(
		None,
		description='Free-text search or raw Firefly III query string. Can be combined with structured filters below.',
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
	account_id: int | None = Field(
		None,
		description='Account ID to filter by (matches source or destination account)',
		examples=[123],
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
		if not any(field is not None for field in search_fields):
			raise ValueError('At least one search criterion must be provided')
		return self


class DeleteTransactionRequest(BaseModel):
	id: str = Field(..., description='Unique identifier of the transaction to permanently remove')


class GetTransactionRequest(BaseModel):
	id: str = Field(..., description='Unique identifier of the transaction to get details for')


class TransactionListResponse(BaseModel):
	"""Response model for transaction listings."""

	transactions: List[Transaction] = Field(
		..., description='Array of transaction objects matching the request'
	)
	total_count: Optional[int] = Field(
		None,
		description='Total transactions available across all pages (if pagination metadata available)',
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

	active: Optional[bool] = Field(
		None,
		description='Show only active budgets (true), inactive budgets (false), or all budgets (not specified)',
	)


class GetBudgetRequest(BaseModel):
	"""Request for getting a single budget by ID."""

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

	start_date: Optional[date] = Field(
		None,
		description='Start date for budget analysis (YYYY-MM-DD format). Defaults to beginning of current month.',
	)
	end_date: Optional[date] = Field(
		None,
		description='End date for budget analysis (YYYY-MM-DD format). Defaults to end of current month.',
	)


class CreateBulkTransactionsRequest(BaseModel):
	"""Create multiple transactions in one operation."""

	transactions: List[Transaction] = Field(
		...,
		description='List of transactions to create (can be mixed types: withdrawals, deposits, transfers)',
		min_length=1,
		max_length=100,
	)


class UpdateTransactionRequest(BaseModel):
	"""Update an existing transaction."""

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

	updates: List[UpdateTransactionRequest] = Field(
		...,
		description='Array of transaction modifications to apply in a single operation',
		min_length=1,
		max_length=50,
	)
