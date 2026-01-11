import logging
from typing import Any, Dict, List

import httpx

from ..config import settings
from ..models.firefly_models import (
	AccountArray,
	AccountSingle,
	AccountTypeFilter,
	AvailableBudgetArray,
	BudgetArray,
	BudgetLimitArray,
	BudgetSingle,
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
	AvailableBudget,
	Budget,
	BudgetSpending,
	BudgetSummary,
	BulkUpdateTransactionsRequest,
	CreateBulkTransactionsRequest,
	CreateDepositRequest,
	CreateTransferRequest,
	CreateWithdrawalRequest,
	DeleteTransactionRequest,
	GetAccountRequest,
	GetAvailableBudgetRequest,
	GetBudgetRequest,
	GetBudgetSpendingRequest,
	GetBudgetSummaryRequest,
	GetTransactionRequest,
	GetTransactionsRequest,
	ListBudgetsRequest,
	SearchAccountRequest,
	SearchTransactionsRequest,
	Transaction,
	UpdateTransactionRequest,
)

logger = logging.getLogger(__name__)


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

	def _serialize_model(self, model: Any, exclude_unset: bool = False) -> Dict[str, Any]:
		"""Serialize a Pydantic model to dict, excluding None values by default.

		Firefly III API rejects None values for many fields, so we exclude them.
		Use exclude_unset=True for update operations to only send changed fields.
		"""
		return model.model_dump(mode='json', exclude_none=True, exclude_unset=exclude_unset)

	def _handle_api_error(
		self, response: httpx.Response, payload: Dict[str, Any] | None = None
	) -> None:
		"""Log detailed error information for API errors.

		Args:
			response: The HTTP response object
			payload: The request payload that was sent (optional, for POST/PUT requests)
		"""
		if response.status_code >= 400:
			logger.error(
				f'Firefly III API error ({response.status_code}): {response.text}',
			)
			if payload:
				logger.error(f'Request payload: {payload}')
			logger.error(f'Request URL: {response.request.url}')

	async def list_accounts(
		self, page: int = 1, type: AccountTypeFilter = AccountTypeFilter.all
	) -> AccountArray:
		r = await self._client.get('/api/v1/accounts', params={'page': page, 'type': type.value})
		self._handle_api_error(r)
		r.raise_for_status()
		return AccountArray.model_validate(r.json())

	async def get_account(self, req: GetAccountRequest) -> Account:
		"""Get a single account by ID."""
		r = await self._client.get(f'/api/v1/accounts/{req.id}')
		self._handle_api_error(r)
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
		self._handle_api_error(r)
		r.raise_for_status()
		return AccountArray.model_validate(r.json())

	@staticmethod
	def _sanitize_value(value: str) -> str:
		"""Escape and optionally quote a search value for Firefly III query syntax.

		Escapes backslashes and double quotes, then wraps the value in double quotes
		if it contains whitespace or quote characters.

		Args:
			value: The raw search value

		Returns:
			Escaped and optionally quoted value safe for Firefly III queries
		"""
		# Escape backslashes first, then escape double quotes
		escaped = value.replace('\\', '\\\\').replace('"', '\\"')

		# Quote if contains whitespace or quote characters
		if ' ' in value or '"' in value or "'" in value:
			return f'"{escaped}"'
		return escaped

	async def search_transactions(self, req: SearchTransactionsRequest) -> TransactionArray:
		"""Search transactions using structured filters or raw query string."""
		# Build query string from structured fields
		query_parts = []

		# Add raw query if provided
		if req.query:
			query_parts.append(req.query)

		# Transaction type and amount filters
		if req.type:
			query_parts.append(f'type:{req.type}')
		if req.amount_equals is not None:
			query_parts.append(f'amount:{req.amount_equals}')
		if req.amount_more is not None:
			query_parts.append(f'more:{req.amount_more}')
		if req.amount_less is not None:
			query_parts.append(f'less:{req.amount_less}')

		# Date filters
		if req.date_on:
			query_parts.append(f'date_on:{req.date_on}')
		if req.date_after:
			query_parts.append(f'date_after:{req.date_after}')
		if req.date_before:
			query_parts.append(f'date_before:{req.date_before}')

		# Content filters
		if req.description_contains:
			query_parts.append(
				f'description_contains:{self._sanitize_value(req.description_contains)}'
			)

		# Metadata filters
		if req.category:
			query_parts.append(f'category_is:{self._sanitize_value(req.category)}')
		if req.budget:
			query_parts.append(f'budget_is:{self._sanitize_value(req.budget)}')

		# Account filters
		if req.account_contains:
			query_parts.append(f'account_contains:{self._sanitize_value(req.account_contains)}')
		if req.account_id is not None:
			query_parts.append(f'account_id:{req.account_id}')

		# Combine all query parts with spaces (AND logic)
		final_query = ' '.join(query_parts)

		params: Dict[str, Any] = {
			'query': final_query,
			'page': req.page,
			'limit': req.limit,
		}

		r = await self._client.get('/api/v1/search/transactions', params=params)
		self._handle_api_error(r)
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
		payload = self._serialize_model(trx_store)
		r = await self._client.post('/api/v1/transactions', json=payload)
		self._handle_api_error(r, payload)
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
		payload = self._serialize_model(trx_store)
		r = await self._client.post('/api/v1/transactions', json=payload)
		self._handle_api_error(r, payload)
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
		payload = self._serialize_model(trx_store)
		r = await self._client.post('/api/v1/transactions', json=payload)
		self._handle_api_error(r, payload)
		r.raise_for_status()
		res = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(res)

	async def create_bulk_transactions(
		self, req: CreateBulkTransactionsRequest
	) -> List[Transaction]:
		"""Create multiple transactions using individual API calls."""
		created_transactions: List[Transaction] = []

		for transaction in req.transactions:
			trx_split = transaction.to_transaction_split_store()
			trx_store = TransactionStore(
				transactions=[trx_split],
				apply_rules=False,
				fire_webhooks=True,
				error_if_duplicate_hash=False,
			)
			payload = self._serialize_model(trx_store)
			r = await self._client.post('/api/v1/transactions', json=payload)
			self._handle_api_error(r, payload)
			r.raise_for_status()
			res = TransactionSingle.model_validate(r.json())
			created_transactions.append(Transaction.from_transaction_single(res))

		return created_transactions

	async def update_transaction(self, req: UpdateTransactionRequest) -> Transaction:
		"""Update an existing transaction with new values."""
		# Build the update payload with only provided fields using explicit parameters
		update_kwargs = {}

		if req.amount is not None:
			update_kwargs['amount'] = str(req.amount)
		if req.description is not None:
			update_kwargs['description'] = req.description
		if req.date is not None:
			update_kwargs['date'] = req.date
		if req.source_id is not None:
			update_kwargs['source_id'] = req.source_id
		if req.destination_id is not None:
			update_kwargs['destination_id'] = req.destination_id
		if req.budget_id is not None:
			update_kwargs['budget_id'] = req.budget_id
		if req.category_name is not None:
			update_kwargs['category_name'] = req.category_name

		trx_split_update = TransactionSplitUpdate(**update_kwargs)

		trx_update = TransactionUpdate(
			apply_rules=False, fire_webhooks=True, group_title=None, transactions=[trx_split_update]
		)

		payload = self._serialize_model(trx_update, exclude_unset=True)
		r = await self._client.put(f'/api/v1/transactions/{req.transaction_id}', json=payload)
		self._handle_api_error(r, payload)
		r.raise_for_status()
		transaction_single = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(transaction_single)

	async def bulk_update_transactions(
		self, req: BulkUpdateTransactionsRequest
	) -> List[Transaction]:
		"""Update multiple transactions using individual API calls."""
		updated_transactions: List[Transaction] = []

		for update_req in req.updates:
			try:
				updated_transaction = await self.update_transaction(update_req)
				updated_transactions.append(updated_transaction)
			except Exception as e:
				# Re-raise with transaction ID context
				raise Exception(
					f'Failed to update transaction {update_req.transaction_id}: {e}'
				) from e

		return updated_transactions

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
		self._handle_api_error(r)
		r.raise_for_status()
		return TransactionArray.model_validate(r.json())

	async def get_account_transactions(self, req: GetTransactionsRequest) -> TransactionArray:
		"""Get transactions for a specific account with optional time range filtering."""
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

		if req.account_id is None:
			raise ValueError('account_id must be provided for account transactions retrieval.')

		r = await self._client.get(f'/api/v1/accounts/{req.account_id}/transactions', params=params)
		self._handle_api_error(r)
		r.raise_for_status()
		return TransactionArray.model_validate(r.json())

	async def get_transaction(self, req: GetTransactionRequest) -> Transaction:
		"""Get a single transaction by ID."""
		r = await self._client.get(f'/api/v1/transactions/{req.id}')
		self._handle_api_error(r)
		r.raise_for_status()
		transaction_single = TransactionSingle.model_validate(r.json())
		return Transaction.from_transaction_single(transaction_single)

	async def delete_transaction(self, req: DeleteTransactionRequest) -> bool:
		"""Delete a transaction by ID."""
		r = await self._client.delete(f'/api/v1/transactions/{req.id}')
		self._handle_api_error(r)
		r.raise_for_status()
		return r.status_code == 204

	async def list_budgets(self, req: ListBudgetsRequest) -> BudgetArray:
		"""List all budgets."""
		r = await self._client.get('/api/v1/budgets')
		self._handle_api_error(r)
		r.raise_for_status()
		budget_array = BudgetArray.model_validate(r.json())
		if req.active is not None:
			budget_array.data = [x for x in budget_array.data if x.attributes.active == req.active]
		return budget_array

	async def get_budget(self, req: GetBudgetRequest) -> Budget:
		"""Get a single budget by ID."""
		r = await self._client.get(f'/api/v1/budgets/{req.id}')
		self._handle_api_error(r)
		r.raise_for_status()
		budget_single = BudgetSingle.model_validate(r.json())
		return Budget.from_budget_read(budget_single.data)

	async def get_budget_spending(self, req: GetBudgetSpendingRequest) -> BudgetSpending:
		"""Get budget spending data for a specific budget and period."""
		params: Dict[str, Any] = {}

		if req.start_date:
			params['start'] = req.start_date.strftime('%Y-%m-%d')
		if req.end_date:
			params['end'] = req.end_date.strftime('%Y-%m-%d')

		# Get budget info first
		budget_r = await self._client.get(f'/api/v1/budgets/{req.budget_id}')
		self._handle_api_error(budget_r)
		budget_r.raise_for_status()
		budget_single = BudgetSingle.model_validate(budget_r.json())
		budget_name = budget_single.data.attributes.name

		# Get spending data from budget limits endpoint
		spending_r = await self._client.get(
			f'/api/v1/budgets/{req.budget_id}/limits', params=params
		)
		self._handle_api_error(spending_r)
		spending_r.raise_for_status()
		limits_array = BudgetLimitArray.model_validate(spending_r.json())

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
		"""Get summary of all budgets with spending information."""
		# Get all budgets
		budgets_r = await self._client.get('/api/v1/budgets')
		self._handle_api_error(budgets_r)
		budgets_r.raise_for_status()
		budgets_array = BudgetArray.model_validate(budgets_r.json())

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
		"""Get available budget for a period."""
		params: Dict[str, Any] = {}

		if req.start_date:
			params['start'] = req.start_date.strftime('%Y-%m-%d')
		if req.end_date:
			params['end'] = req.end_date.strftime('%Y-%m-%d')

		r = await self._client.get('/api/v1/available-budgets', params=params)
		self._handle_api_error(r)
		r.raise_for_status()
		available_array = AvailableBudgetArray.model_validate(r.json())

		# Parse the available budget data
		if available_array.data:
			first_budget = available_array.data[0]
			return AvailableBudget(
				amount=float(first_budget.attributes.amount),
				currency_code=first_budget.attributes.currency_code or 'USD',
				start_date=req.start_date or first_budget.attributes.start.date(),
				end_date=req.end_date or first_budget.attributes.end.date(),
			)
		else:
			# Return default if no data available
			from datetime import date

			today = date.today()
			return AvailableBudget(
				amount=0.0,
				currency_code='USD',
				start_date=req.start_date or today.replace(day=1),
				end_date=req.end_date or today,
			)
