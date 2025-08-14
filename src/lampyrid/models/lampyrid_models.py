from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .firefly_models import (
	AccountRead,
	AccountTypeFilter,
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


class TransactionType(Enum):
	withdrawal = 'withdrawal'
	deposit = 'deposit'
	transfer = 'transfer'


class Transaction(BaseModel):
	amount: float = Field(..., description='Amount of the transaction')
	description: str = Field(..., description='Description of the transaction')
	type: TransactionType = Field(..., description='Type of the transaction')
	date: datetime = Field(
		default_factory=datetime.now, description='Date and time of the transaction'
	)
	source_id: str = Field(
		...,
		description='ID of the source account. For a withdrawal or a transfer, this must always be an asset account. For deposits, this must be a revenue account.',
	)
	destination_id: str = Field(
		...,
		description='ID of the destination account. For a deposit or a transfer, this must always be an asset account. For withdrawals this must be an expense account.',
	)

	@classmethod
	def from_transaction_single(cls, trx: TransactionSingle) -> 'Transaction':
		inner_trx = trx.data.attributes.transactions[0]
		return cls(
			amount=float(inner_trx.amount),
			description=inner_trx.description,
			type=TransactionType[inner_trx.type.value],
			date=inner_trx.date,
			source_id=inner_trx.source_id,
			destination_id=inner_trx.destination_id,
		)

	def to_transaction_split_store(self) -> TransactionSplitStore:
		return TransactionSplitStore(
			type=TransactionTypeProperty(self.type.value),
			date=self.date,
			amount=str(self.amount),
			description=self.description,
		)


class ListAccountRequest(BaseModel):
	type: AccountTypeFilter = Field(..., description='Type of account to filter by')


class SearchAccountRequest(BaseModel):
	query: str = Field(..., description='Search query for account names')
	type: AccountTypeFilter = Field(
		AccountTypeFilter.all, description='Optional type filter for accounts'
	)


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


class TransactionSummary(BaseModel):
	"""Simplified transaction model for listing transactions."""

	id: str = Field(..., description='Transaction ID')
	description: str = Field(..., description='Transaction description')
	amount: float = Field(..., description='Transaction amount')
	date: datetime = Field(..., description='Transaction date')
	type: str = Field(..., description='Transaction type (withdrawal, deposit, transfer)')
	source_name: Optional[str] = Field(None, description='Source account name')
	destination_name: Optional[str] = Field(None, description='Destination account name')
	currency_code: Optional[str] = Field(None, description='Currency code')

	@classmethod
	def from_transaction_read(cls, transaction_read: TransactionRead) -> 'TransactionSummary':
		"""Create a TransactionSummary from a Firefly TransactionRead object."""
		first_trx = transaction_read.attributes.transactions[0]
		return cls(
			id=transaction_read.id,
			description=first_trx.description,
			amount=float(first_trx.amount),
			date=first_trx.date,
			type=first_trx.type.value if first_trx.type else 'unknown',
			source_name=first_trx.source_name,
			destination_name=first_trx.destination_name,
			currency_code=first_trx.currency_code,
		)


class TransactionListResponse(BaseModel):
	"""Response model for transaction listings."""

	transactions: List[TransactionSummary] = Field(..., description='List of transactions')
	total_count: Optional[int] = Field(None, description='Total number of transactions available')
	current_page: int = Field(..., description='Current page number')
	per_page: int = Field(..., description='Number of items per page')

	@classmethod
	def from_transaction_array(
		cls, transaction_array: TransactionArray, current_page: int, per_page: int
	) -> 'TransactionListResponse':
		"""Create a TransactionListResponse from a Firefly TransactionArray."""
		transactions = [
			TransactionSummary.from_transaction_read(trx_read)
			for trx_read in transaction_array.data
		]
		return cls(
			transactions=transactions,
			total_count=transaction_array.meta.pagination.total
			if transaction_array.meta.pagination
			else None,
			current_page=current_page,
			per_page=per_page,
		)
