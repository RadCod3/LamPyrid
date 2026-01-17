"""HTTP client for interacting with the Firefly III API."""

import logging
from datetime import date
from typing import Any, Dict, Optional

import httpx

from ..config import settings
from ..models.firefly_models import (
    AccountArray,
    AccountSingle,
    AccountStore,
    AccountTypeFilter,
    AvailableBudgetArray,
    BudgetArray,
    BudgetLimitArray,
    BudgetSingle,
    BudgetStore,
    TransactionArray,
    TransactionSingle,
    TransactionStore,
    TransactionUpdate,
)

logger = logging.getLogger(__name__)


class FireflyClient:
    """HTTP client for interacting with the Firefly III API."""

    def __init__(self) -> None:
        """Initialize the Firefly III API client with authentication headers."""
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
        """List accounts with optional pagination and type filtering."""
        r = await self._client.get('/api/v1/accounts', params={'page': page, 'type': type.value})
        self._handle_api_error(r)
        r.raise_for_status()
        return AccountArray.model_validate(r.json())

    async def get_account(self, account_id: str) -> AccountSingle:
        """Get a single account by ID."""
        r = await self._client.get(f'/api/v1/accounts/{account_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return AccountSingle.model_validate(r.json())

    async def search_accounts(self, query: str, type: AccountTypeFilter) -> AccountArray:
        """Search accounts by name with optional type filtering."""
        r = await self._client.get(
            '/api/v1/search/accounts',
            params={
                'query': query,
                'type': type.value,
                'field': 'name',
                'limit': 50,
                'page': 1,
            },
        )
        self._handle_api_error(r)
        r.raise_for_status()
        return AccountArray.model_validate(r.json())

    async def create_account(self, account_store: AccountStore) -> AccountSingle:
        """Create a new account in Firefly III."""
        r = await self._client.post('/api/v1/accounts', json=self._serialize_model(account_store))
        self._handle_api_error(r)
        r.raise_for_status()
        return AccountSingle.model_validate(r.json())

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

    async def search_transactions(
        self, query: str, page: int = 1, limit: int = 50
    ) -> TransactionArray:
        """Search transactions using a query string."""
        params: Dict[str, Any] = {
            'query': query,
            'page': page,
            'limit': limit,
        }

        r = await self._client.get('/api/v1/search/transactions', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return TransactionArray.model_validate(r.json())

    async def create_transaction(self, transaction_store: TransactionStore) -> TransactionSingle:
        """Create a transaction with the given store data."""
        payload = self._serialize_model(transaction_store)
        r = await self._client.post('/api/v1/transactions', json=payload)
        self._handle_api_error(r, payload)
        r.raise_for_status()
        return TransactionSingle.model_validate(r.json())

    async def update_transaction(
        self, transaction_id: str, transaction_update: TransactionUpdate
    ) -> TransactionSingle:
        """Update an existing transaction."""
        payload = self._serialize_model(transaction_update, exclude_unset=True)
        r = await self._client.put(f'/api/v1/transactions/{transaction_id}', json=payload)
        self._handle_api_error(r, payload)
        r.raise_for_status()
        return TransactionSingle.model_validate(r.json())

    async def get_transactions(
        self,
        page: int = 1,
        limit: int = 50,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[str] = None,
    ) -> TransactionArray:
        """Get transactions with optional filtering."""
        params: Dict[str, Any] = {
            'page': page,
            'limit': limit,
        }

        if start_date:
            params['start'] = start_date.strftime('%Y-%m-%d')

        if end_date:
            params['end'] = end_date.strftime('%Y-%m-%d')

        if transaction_type:
            params['type'] = transaction_type

        r = await self._client.get('/api/v1/transactions', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return TransactionArray.model_validate(r.json())

    async def get_account_transactions(
        self,
        account_id: str,
        page: int = 1,
        limit: int = 50,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[str] = None,
    ) -> TransactionArray:
        """Get transactions for a specific account."""
        params: Dict[str, Any] = {
            'page': page,
            'limit': limit,
        }

        if start_date:
            params['start'] = start_date.strftime('%Y-%m-%d')

        if end_date:
            params['end'] = end_date.strftime('%Y-%m-%d')

        if transaction_type:
            params['type'] = transaction_type

        r = await self._client.get(f'/api/v1/accounts/{account_id}/transactions', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return TransactionArray.model_validate(r.json())

    async def get_transaction(self, transaction_id: str) -> TransactionSingle:
        """Get a single transaction by ID."""
        r = await self._client.get(f'/api/v1/transactions/{transaction_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return TransactionSingle.model_validate(r.json())

    async def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction by ID."""
        r = await self._client.delete(f'/api/v1/transactions/{transaction_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return r.status_code == 204

    async def get_budgets(self) -> BudgetArray:
        """Get all budgets."""
        r = await self._client.get('/api/v1/budgets')
        self._handle_api_error(r)
        r.raise_for_status()
        return BudgetArray.model_validate(r.json())

    async def get_budget(self, budget_id: str) -> BudgetSingle:
        """Get a single budget by ID."""
        r = await self._client.get(f'/api/v1/budgets/{budget_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return BudgetSingle.model_validate(r.json())

    async def get_budget_limits(
        self, budget_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> BudgetLimitArray:
        """Get budget limits for a specific budget and period."""
        params: Dict[str, Any] = {}

        if start_date:
            params['start'] = start_date.strftime('%Y-%m-%d')
        if end_date:
            params['end'] = end_date.strftime('%Y-%m-%d')

        r = await self._client.get(f'/api/v1/budgets/{budget_id}/limits', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return BudgetLimitArray.model_validate(r.json())

    async def create_budget(self, budget_store: BudgetStore) -> BudgetSingle:
        """Create a new budget."""
        payload = self._serialize_model(budget_store)
        r = await self._client.post('/api/v1/budgets', json=payload)
        self._handle_api_error(r, payload)
        r.raise_for_status()
        return BudgetSingle.model_validate(r.json())

    async def get_available_budgets(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> AvailableBudgetArray:
        """Get available budgets for a period."""
        params: Dict[str, Any] = {}

        if start_date:
            params['start'] = start_date.strftime('%Y-%m-%d')
        if end_date:
            params['end'] = end_date.strftime('%Y-%m-%d')

        r = await self._client.get('/api/v1/available-budgets', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return AvailableBudgetArray.model_validate(r.json())
