from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .firefly_models import (
	AccountRead,
	AccountTypeFilter,
	TransactionSingle,
	TransactionSplitStore,
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
			type=TransactionTypeProperty(self.type),
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
