from typing import Any, Dict

import httpx

from ..config import settings
from ..models.firefly_models import (
	AccountArray,
	AccountSingle,
	AccountTypeFilter,
	BudgetArray,
	TransactionArray,
	TransactionSingle,
	TransactionSplitStore,
	TransactionSplitUpdate,
	TransactionStore,
	TransactionTypeProperty,
	TransactionUpdate,
)
from ..models.lampyrid_models import (
	Account,
	CreateDepositRequest,
	CreateTransferRequest,
	CreateWithdrawalRequest,
	DeleteTransactionRequest,
	GetAccountRequest,
	GetTransactionRequest,
	GetTransactionsRequest,
	ListBudgetsRequest,
	SearchAccountRequest,
	SearchTransactionsRequest,
	Transaction,
	UpdateTransactionBudgetRequest,
)


class FireflyClient:
	def __init__(self) -> None:
		base = str(settings.firefly_base_url).rstrip('/')
		self._client = httpx.AsyncClient(
			base_url=base,
			headers={
				'Authorization': f'Bearer {settings.firefly_token}',
				'Accept': 'application/json',
				'Content-Type': 'application/json',
			},
			timeout=30.0,
		)

	async def list_accounts(
		self, page: int = 1, type: AccountTypeFilter = AccountTypeFilter.all
	) -> AccountArray:
		r = await self._client.get('/api/v1/accounts', params={'page': page, 'type': type.value})
		r.raise_for_status()
		return AccountArray.model_validate(r.json())

	async def get_account(self, req: GetAccountRequest) -> Account:
		"""Get a single account by ID."""
		r = await self._client.get(f'/api/v1/accounts/{req.id}')
		r.raise_for_status()
		account_single = AccountSingle.model_validate(r.json())
		return Account.from_account_read(account_single.data)

	async def search_accounts(self, req: SearchAccountRequest) -> AccountArray:
		r = await self._client.get(
			'/api/v1/search/accounts',
			params={
				'query': req.query,
				'type': req.type.value,
				'field': 'name',
				'limit': 50,
				'page': 1,
			},
		)

		r.raise_for_status()
		return AccountArray.model_validate(r.json())

	async def search_transactions(self, req: SearchTransactionsRequest) -> TransactionArray:
		"""Search transactions by description or other text fields."""
		params: Dict[str, Any] = {
			'query': req.query,
			'page': req.page,
			'limit': req.limit,
		}

		r = await self._client.get('/api/v1/search/transactions', params=params)
		r.raise_for_status()
		return TransactionArray.model_validate(r.json())

	async def create_withdrawal(self, withdrawal: CreateWithdrawalRequest) -> Transaction:
		trx = TransactionSplitStore(
			amount=str(withdrawal.amount),
			description=withdrawal.description,
			type=TransactionTypeProperty.withdrawal,
			date=withdrawal.date,
			source_id=withdrawal.source_id,
			destination_name=withdrawal.destination_name,
			budget_id=withdrawal.budget_id,
			budget_name=withdrawal.budget_name,
		)
		trx_store = TransactionStore(transactions=[trx])
		print(f'Creating withdrawal: {trx_store.model_dump_json()}')
		r = await self._client.post('/api/v1/transactions', json=trx_store.model_dump(mode='json'))
		r.raise_for_status()
		res = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(res)

	async def create_deposit(self, deposit: CreateDepositRequest) -> Transaction:
		trx = TransactionSplitStore(
			amount=str(deposit.amount),
			description=deposit.description,
			type=TransactionTypeProperty.deposit,
			date=deposit.date,
			source_name=deposit.source_name,
			destination_id=deposit.destination_id,
		)
		trx_store = TransactionStore(transactions=[trx])
		r = await self._client.post('/api/v1/transactions', json=trx_store.model_dump(mode='json'))
		r.raise_for_status()
		res = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(res)

	async def create_transfer(self, transfer: CreateTransferRequest) -> Transaction:
		trx = TransactionSplitStore(
			amount=str(transfer.amount),
			description=transfer.description,
			type=TransactionTypeProperty.transfer,
			date=transfer.date,
			source_id=transfer.source_id,
			destination_id=transfer.destination_id,
		)
		trx_store = TransactionStore(transactions=[trx])
		r = await self._client.post('/api/v1/transactions', json=trx_store.model_dump(mode='json'))
		r.raise_for_status()
		res = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(res)

	async def get_transactions(self, req: GetTransactionsRequest) -> TransactionArray:
		"""Get transactions with optional time range and type filtering."""
		params: Dict[str, Any] = {
			'page': req.page,
			'limit': req.limit,
		}

		if req.start_date:
			params['start'] = req.start_date.strftime('%Y-%m-%d')

		if req.end_date:
			params['end'] = req.end_date.strftime('%Y-%m-%d')

		if req.transaction_type:
			params['type'] = req.transaction_type.value

		r = await self._client.get('/api/v1/transactions', params=params)
		r.raise_for_status()
		return TransactionArray.model_validate(r.json())

	async def get_transaction(self, req: GetTransactionRequest) -> Transaction:
		"""Get a single transaction by ID."""
		r = await self._client.get(f'/api/v1/transactions/{req.id}')
		r.raise_for_status()
		transaction_single = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(transaction_single)

	async def delete_transaction(self, req: DeleteTransactionRequest) -> bool:
		"""Delete a transaction by ID."""
		r = await self._client.delete(f'/api/v1/transactions/{req.id}')
		r.raise_for_status()
		return r.status_code == 204

	async def list_budgets(self, req: ListBudgetsRequest) -> BudgetArray:
		"""List all budgets."""
		params: Dict[str, Any] = {}

		if req.active is not None:
			params['active'] = req.active

		r = await self._client.get('/api/v1/budgets', params=params)
		r.raise_for_status()
		return BudgetArray.model_validate(r.json())

	async def update_transaction_budget(self, req: UpdateTransactionBudgetRequest) -> Transaction:
		"""Update a transaction's budget allocation."""
		# Create the transaction update payload
		trx_split_update = TransactionSplitUpdate(
			budget_id=req.budget_id,
			budget_name=req.budget_name,
		)

		trx_update = TransactionUpdate(
			apply_rules=False, fire_webhooks=True, group_title=None, transactions=[trx_split_update]
		)

		r = await self._client.put(
			f'/api/v1/transactions/{req.transaction_id}',
			json=trx_update.model_dump(mode='json', exclude_unset=True),
		)
		r.raise_for_status()
		transaction_single = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(transaction_single)
