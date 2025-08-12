from typing import Any, Dict

import httpx

from ..config import settings
from ..models.firefly_models import (
	AccountArray,
	AccountTypeFilter,
	TransactionSingle,
	TransactionSplitStore,
	TransactionStore,
	TransactionTypeProperty,
)
from ..models.lampyrid_models import CreateWithdrawalRequest, SearchAccountRequest, Transaction


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

	async def search_transactions(self, query: str, page: int = 1) -> Dict[str, Any]:
		r = await self._client.get('/api/v1/transactions', params={'query': query, 'page': page})
		r.raise_for_status()
		return r.json()

	async def create_transaction(self, transaction: Transaction) -> TransactionSingle:
		trx_split_store = TransactionSplitStore.from_lampyrid_transaction(transaction)
		trx_store = TransactionStore(transactions=[trx_split_store])
		r = await self._client.post('/api/v1/transactions', json=trx_store.model_dump())
		r.raise_for_status()
		return TransactionSingle.model_validate(r.json())

	async def create_withdrawal(self, withdrawal: CreateWithdrawalRequest) -> Transaction:
		trx = TransactionSplitStore(
			amount=str(withdrawal.amount),
			description=withdrawal.description,
			type=TransactionTypeProperty.withdrawal,
			date=withdrawal.date,
		)
		trx_store = TransactionStore(transactions=[trx])
		r = await self._client.post('/api/v1/transactions', json=trx_store.model_dump())
		r.raise_for_status()
		res = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(res)


	# async def aclose(self) -> None:
	# 	await self._client.aclose()
