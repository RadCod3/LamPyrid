from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

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
	id: str = Field(..., examples=['2'])
	name: str = Field(..., examples=['Cash'])
	currency_code: Optional[str] = Field(None, examples=['GBP'])
	current_balance: Optional[float] = Field(None, examples=[1000.0])

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
	id: str = Field(..., examples=['2'])
	name: str = Field(..., examples=['Groceries'])
	active: Optional[bool] = Field(None, examples=[True])
	notes: Optional[str] = Field(None, examples=['Monthly grocery budget'])
	order: Optional[int] = Field(None, examples=[1])

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
	type: AccountTypeFilter = Field(..., description='Type of account to filter by')


class SearchAccountRequest(BaseModel):
	query: str = Field(..., description='Search query for account names')
	type: AccountTypeFilter = Field(
		AccountTypeFilter.all, description='Optional type filter for accounts'
	)


class GetAccountRequest(BaseModel):
	id: str = Field(..., description='ID of the account to retrieve')


class CreateWithdrawalRequest(BaseModel):
	amount: float = Field(..., description='Amount of the withdrawal')
	description: str = Field(..., description='Description of the withdrawal')
	date: datetime = Field(default_factory=utc_now, description='Date and time of the withdrawal')
	source_id: str = Field(
		...,
		description='ID of the source account for the withdrawal. This must always be an asset account.',
	)
	destination_name: Optional[str] = Field(
		default=None,
		description='Name of the destination account for the withdrawal. This account is automatically created if it does not exist. Leave it blank for cash withdrawals.',
	)
	budget_id: Optional[str] = Field(
		None, description='ID of the budget to allocate this withdrawal to'
	)
	budget_name: Optional[str] = Field(
		None,
		description='Name of the budget to allocate this withdrawal to. If the budget name is unknown, the ID will be used or the value will be ignored.',
	)


class CreateDepositRequest(BaseModel):
	amount: float = Field(..., description='Amount of the deposit')
	description: str = Field(..., description='Description of the deposit')
	date: datetime = Field(default_factory=utc_now, description='Date and time of the deposit')
	source_name: Optional[str] = Field(
		default=None,
		description='Name of the source account for the deposit. This account is automatically created if it does not exist.',
	)
	destination_id: str = Field(
		...,
		description='ID of the destination account for the deposit. This must always be an asset account.',
	)


class CreateTransferRequest(BaseModel):
	amount: float = Field(..., description='Amount of the transfer')
	description: str = Field(..., description='Description of the transfer')
	date: datetime = Field(default_factory=utc_now, description='Date and time of the transfer')
	source_id: str = Field(
		...,
		description='ID of the source account for the transfer. This must always be an asset account.',
	)
	destination_id: str = Field(
		...,
		description='ID of the destination account for the transfer. This must always be an asset account.',
	)


class GetTransactionsRequest(BaseModel):
	start_date: Optional[date] = Field(
		None, description='Start date for transaction range (YYYY-MM-DD), inclusive'
	)
	end_date: Optional[date] = Field(
		None, description='End date for transaction range (YYYY-MM-DD), inclusive'
	)
	transaction_type: Optional[TransactionTypeFilter] = Field(
		None, description='Optional filter on transaction type'
	)
	page: Optional[int] = Field(1, description='Page number for pagination', ge=1)
	limit: Optional[int] = Field(50, description='Number of items per page', ge=1, le=500)


class SearchTransactionsRequest(BaseModel):
	query: str = Field(
		..., description='Search query to find transactions (e.g., "groceries", "salary")'
	)
	page: Optional[int] = Field(1, description='Page number for pagination', ge=1)
	limit: Optional[int] = Field(50, description='Number of items per page', ge=1, le=500)


class DeleteTransactionRequest(BaseModel):
	id: str = Field(..., description='ID of the transaction to delete')


class GetTransactionRequest(BaseModel):
	id: str = Field(..., description='ID of the transaction to retrieve')


class TransactionListResponse(BaseModel):
	"""Response model for transaction listings."""

	transactions: List[Transaction] = Field(..., description='List of transactions')
	total_count: Optional[int] = Field(None, description='Total number of transactions available')
	current_page: int = Field(..., description='Current page number')
	per_page: int = Field(..., description='Number of items per page')

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

	active: Optional[bool] = Field(None, description='Filter budgets by active status')


class UpdateTransactionBudgetRequest(BaseModel):
	"""Request for updating a transaction's budget allocation."""

	transaction_id: str = Field(..., description='ID of the transaction to update')
	budget_id: Optional[str] = Field(
		None,
		description='ID of the budget to allocate the transaction to. Set to None to remove budget allocation.',
	)
	budget_name: Optional[str] = Field(
		None,
		description='Name of the budget to allocate the transaction to. If the budget name is unknown, the ID will be used or the value will be ignored.',
	)


class GetBudgetRequest(BaseModel):
	"""Request for getting a single budget by ID."""

	id: str = Field(..., description='ID of the budget to retrieve')


class BudgetSpending(BaseModel):
	"""Budget spending information for a specific period."""

	budget_id: str = Field(..., description='ID of the budget')
	budget_name: str = Field(..., description='Name of the budget')
	spent: float = Field(..., description='Amount spent in this budget during the period')
	budgeted: Optional[float] = Field(None, description='Budgeted amount for this period')
	remaining: Optional[float] = Field(None, description='Remaining budget amount')
	percentage_spent: Optional[float] = Field(None, description='Percentage of budget spent')


class GetBudgetSpendingRequest(BaseModel):
	"""Request for getting budget spending data."""

	budget_id: str = Field(..., description='ID of the budget to get spending for')
	start_date: Optional[date] = Field(
		None, description='Start date for spending period (YYYY-MM-DD), inclusive'
	)
	end_date: Optional[date] = Field(
		None, description='End date for spending period (YYYY-MM-DD), inclusive'
	)


class BudgetSummary(BaseModel):
	"""Summary of all budgets with spending information."""

	budgets: List[BudgetSpending] = Field(..., description='List of budget spending data')
	total_budgeted: Optional[float] = Field(None, description='Total budgeted amount')
	total_spent: float = Field(..., description='Total amount spent across all budgets')
	total_remaining: Optional[float] = Field(None, description='Total remaining budget')
	available_budget: Optional[float] = Field(
		None, description='Available budget amount not allocated to specific budgets'
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

	amount: float = Field(..., description='Available budget amount')
	currency_code: str = Field(..., description='Currency code for the amount')
	start_date: date = Field(..., description='Start date of the budget period')
	end_date: date = Field(..., description='End date of the budget period')


class GetAvailableBudgetRequest(BaseModel):
	"""Request for getting available budget."""

	start_date: Optional[date] = Field(
		None, description='Start date for budget period (YYYY-MM-DD), defaults to current month'
	)
	end_date: Optional[date] = Field(
		None, description='End date for budget period (YYYY-MM-DD), defaults to current month'
	)


class CreateBulkTransactionsRequest(BaseModel):
	"""Create multiple transactions in one operation."""

	transactions: List[Transaction] = Field(
		...,
		description='List of transactions to create (can be mixed types: withdrawals, deposits, transfers)',
		min_length=1,
		max_length=100,
	)
