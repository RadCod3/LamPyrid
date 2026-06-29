"""HTTP client for interacting with the Firefly III API."""

import logging
from datetime import date
from typing import Any, Dict, Optional
from urllib.parse import quote

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
    BudgetLimitSingle,
    BudgetLimitStore,
    BudgetLimitUpdate,
    BudgetSingle,
    BudgetStore,
    CategoryArray,
    CategorySingle,
    InsightGroup,
    InsightTotal,
    InsightTransfer,
    RuleArray,
    RuleSingle,
    RuleUpdate,
    TagArray,
    TagSingle,
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
        # Append the API prefix here so individual methods use relative paths.
        # Note: the trailing slash is required for httpx to join relative paths
        # correctly (e.g. base '.../api/v1/' + 'accounts' -> '.../api/v1/accounts').
        self._client = httpx.AsyncClient(
            base_url=f'{base}/api/v1/',
            headers={
                'Authorization': f'Bearer {settings.firefly_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            timeout=30.0,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client.

        Should be called when the client is no longer needed to release resources.
        Alternatively, use the client as an async context manager.
        """
        await self._client.aclose()

    async def __aenter__(self) -> 'FireflyClient':
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - close the client."""
        await self.aclose()

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
        r = await self._client.get('accounts', params={'page': page, 'type': type.value})
        self._handle_api_error(r)
        r.raise_for_status()
        return AccountArray.model_validate(r.json())

    async def get_account(self, account_id: str) -> AccountSingle:
        """Get a single account by ID."""
        r = await self._client.get(f'accounts/{account_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return AccountSingle.model_validate(r.json())

    async def search_accounts(self, query: str, type: AccountTypeFilter) -> AccountArray:
        """Search accounts by name with optional type filtering."""
        r = await self._client.get(
            'search/accounts',
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
        r = await self._client.post('accounts', json=self._serialize_model(account_store))
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

        r = await self._client.get('search/transactions', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return TransactionArray.model_validate(r.json())

    async def create_transaction(self, transaction_store: TransactionStore) -> TransactionSingle:
        """Create a transaction with the given store data."""
        payload = self._serialize_model(transaction_store)
        r = await self._client.post('transactions', json=payload)
        self._handle_api_error(r, payload)
        r.raise_for_status()
        return TransactionSingle.model_validate(r.json())

    async def update_transaction(
        self, transaction_id: str, transaction_update: TransactionUpdate
    ) -> TransactionSingle:
        """Update an existing transaction."""
        payload = self._serialize_model(transaction_update, exclude_unset=True)
        r = await self._client.put(f'transactions/{transaction_id}', json=payload)
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

        r = await self._client.get('transactions', params=params)
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

        r = await self._client.get(f'accounts/{account_id}/transactions', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return TransactionArray.model_validate(r.json())

    async def get_transaction(self, transaction_id: str) -> TransactionSingle:
        """Get a single transaction by ID."""
        r = await self._client.get(f'transactions/{transaction_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return TransactionSingle.model_validate(r.json())

    async def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction by ID."""
        r = await self._client.delete(f'transactions/{transaction_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return r.status_code == 204

    async def get_budgets(self) -> BudgetArray:
        """Get all budgets."""
        r = await self._client.get('budgets')
        self._handle_api_error(r)
        r.raise_for_status()
        return BudgetArray.model_validate(r.json())

    async def get_budget(self, budget_id: str) -> BudgetSingle:
        """Get a single budget by ID."""
        r = await self._client.get(f'budgets/{budget_id}')
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

        r = await self._client.get(f'budgets/{budget_id}/limits', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return BudgetLimitArray.model_validate(r.json())

    async def create_budget_limit(
        self, budget_id: str, budget_limit_store: BudgetLimitStore
    ) -> BudgetLimitSingle:
        """Create a budget limit for a budget."""
        payload = self._serialize_model(budget_limit_store)
        r = await self._client.post(f'budgets/{budget_id}/limits', json=payload)
        self._handle_api_error(r, payload)
        r.raise_for_status()
        return BudgetLimitSingle.model_validate(r.json())

    async def update_budget_limit(
        self, budget_id: str, limit_id: str, budget_limit_update: BudgetLimitUpdate
    ) -> BudgetLimitSingle:
        """Update an existing budget limit."""
        payload = self._serialize_model(budget_limit_update, exclude_unset=True)
        r = await self._client.put(f'budgets/{budget_id}/limits/{limit_id}', json=payload)
        self._handle_api_error(r, payload)
        r.raise_for_status()
        return BudgetLimitSingle.model_validate(r.json())

    async def delete_budget_limit(self, budget_id: str, limit_id: str) -> bool:
        """Delete a budget limit by ID."""
        r = await self._client.delete(f'budgets/{budget_id}/limits/{limit_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return r.status_code == 204

    async def create_budget(self, budget_store: BudgetStore) -> BudgetSingle:
        """Create a new budget."""
        payload = self._serialize_model(budget_store)
        r = await self._client.post('budgets', json=payload)
        self._handle_api_error(r, payload)
        r.raise_for_status()
        return BudgetSingle.model_validate(r.json())

    async def delete_budget(self, budget_id: str) -> bool:
        """Delete a budget by ID."""
        r = await self._client.delete(f'budgets/{budget_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return r.status_code == 204

    async def get_available_budgets(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> AvailableBudgetArray:
        """Get available budgets for a period."""
        params: Dict[str, Any] = {}

        if start_date:
            params['start'] = start_date.strftime('%Y-%m-%d')
        if end_date:
            params['end'] = end_date.strftime('%Y-%m-%d')

        r = await self._client.get('available-budgets', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return AvailableBudgetArray.model_validate(r.json())

    # =========================================================================
    # Category API Methods
    # =========================================================================

    async def get_categories(self, page: int = 1) -> CategoryArray:
        """Get all categories."""
        r = await self._client.get('categories', params={'page': page})
        self._handle_api_error(r)
        r.raise_for_status()
        return CategoryArray.model_validate(r.json())

    async def get_category(
        self,
        category_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> CategorySingle:
        """Get a single category by ID.

        When start_date and end_date are provided, the response includes spending
        and earning totals for that period.
        """
        params: Dict[str, Any] = {}
        if start_date:
            params['start'] = start_date.strftime('%Y-%m-%d')
        if end_date:
            params['end'] = end_date.strftime('%Y-%m-%d')

        r = await self._client.get(f'categories/{category_id}', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return CategorySingle.model_validate(r.json())

    # =========================================================================
    # Tag API Methods
    # =========================================================================

    async def get_tags(self, page: int = 1) -> TagArray:
        """Get all tags."""
        r = await self._client.get('tags', params={'page': page})
        self._handle_api_error(r)
        r.raise_for_status()
        return TagArray.model_validate(r.json())

    async def get_tag(self, tag: str) -> TagSingle:
        """Get a single tag by its name or numeric ID."""
        # Encode as a single path segment: tag names may contain '/', '?', '#', etc.
        r = await self._client.get(f'tags/{quote(tag, safe="")}')
        self._handle_api_error(r)
        r.raise_for_status()
        return TagSingle.model_validate(r.json())

    # =========================================================================
    # Insight API Methods
    # =========================================================================

    def _build_insight_params(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> Dict[str, Any]:
        """Build common parameters for insight API calls."""
        params: Dict[str, Any] = {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        }
        if account_ids:
            params['accounts[]'] = account_ids
        return params

    # Expense Insight Methods

    async def get_expense_total(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightTotal:
        """Get total expenses for a period."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/expense/total', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightTotal.model_validate(r.json())

    async def get_expense_by_expense_account(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightGroup:
        """Get expenses grouped by expense account (vendor/payee)."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/expense/expense', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightGroup.model_validate(r.json())

    async def get_expense_by_asset_account(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightGroup:
        """Get expenses grouped by asset account (source)."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/expense/asset', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightGroup.model_validate(r.json())

    async def get_expense_by_budget(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
        budget_ids: Optional[list[int]] = None,
    ) -> InsightGroup:
        """Get expenses grouped by budget."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        if budget_ids:
            params['budgets[]'] = budget_ids
        r = await self._client.get('insight/expense/budget', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightGroup.model_validate(r.json())

    async def get_expense_no_budget(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightTotal:
        """Get expenses without any budget assigned."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/expense/no-budget', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightTotal.model_validate(r.json())

    # Income Insight Methods

    async def get_income_total(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightTotal:
        """Get total income for a period."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/income/total', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightTotal.model_validate(r.json())

    async def get_income_by_revenue_account(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightGroup:
        """Get income grouped by revenue account (income source)."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/income/revenue', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightGroup.model_validate(r.json())

    async def get_income_by_asset_account(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightGroup:
        """Get income grouped by asset account (receiving account)."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/income/asset', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightGroup.model_validate(r.json())

    # Transfer Insight Methods

    async def get_transfer_total(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightTotal:
        """Get total transfers for a period."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/transfer/total', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightTotal.model_validate(r.json())

    async def get_transfer_by_asset_account(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[int]] = None,
    ) -> InsightTransfer:
        """Get transfers grouped by asset account with in/out breakdown."""
        params = self._build_insight_params(start_date, end_date, account_ids)
        r = await self._client.get('insight/transfer/asset', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return InsightTransfer.model_validate(r.json())

    # =========================================================================
    # Rule Management Methods
    # =========================================================================

    async def get_rules(self, page: int = 1) -> RuleArray:
        """Get all rules with pagination."""
        r = await self._client.get('rules', params={'page': page})
        self._handle_api_error(r)
        r.raise_for_status()
        return RuleArray.model_validate(r.json())

    async def get_rule(self, rule_id: str) -> RuleSingle:
        """Get a single rule by ID."""
        r = await self._client.get(f'rules/{rule_id}')
        self._handle_api_error(r)
        r.raise_for_status()
        return RuleSingle.model_validate(r.json())

    async def update_rule(self, rule_id: str, rule_update: RuleUpdate) -> RuleSingle:
        """Update an existing rule."""
        payload = self._serialize_model(rule_update, exclude_unset=True)
        r = await self._client.put(f'rules/{rule_id}', json=payload)
        self._handle_api_error(r, payload)
        r.raise_for_status()
        return RuleSingle.model_validate(r.json())

    async def test_rule(
        self,
        rule_id: str,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[str]] = None,
    ) -> TransactionArray:
        """Test a rule in preview mode (shows matches without changes).

        Args:
            rule_id: ID of the rule to test
            start_date: Start date for matching transactions
            end_date: End date for matching transactions
            account_ids: Optional list of account IDs to filter

        Returns:
            TransactionArray with matching transactions

        """
        params: Dict[str, Any] = {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        }
        if account_ids:
            params['accounts[]'] = account_ids

        r = await self._client.get(f'rules/{rule_id}/test', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return TransactionArray.model_validate(r.json())

    async def trigger_rule(
        self,
        rule_id: str,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[str]] = None,
    ) -> bool:
        """Execute a rule (applies changes to matching transactions).

        Args:
            rule_id: ID of the rule to execute
            start_date: Start date for matching transactions
            end_date: End date for matching transactions
            account_ids: Optional list of account IDs to filter

        Returns:
            True if the rule execution was accepted (processing is async)

        """
        params: Dict[str, Any] = {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        }
        if account_ids:
            params['accounts[]'] = account_ids

        r = await self._client.post(f'rules/{rule_id}/trigger', params=params)
        self._handle_api_error(r)
        r.raise_for_status()
        return r.status_code == 204
