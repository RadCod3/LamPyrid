"""
Test configuration and shared fixtures for LamPyrid integration tests.

This module provides pytest fixtures for:
- FireflyClient instance configured for testing
- Test accounts (asset, expense, revenue)
- Test budgets
- Transaction cleanup utilities
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import httpx
import pytest
from dotenv import load_dotenv

from lampyrid.models.firefly_models import (
	AccountRoleProperty,
	AccountRolePropertyEnum,
	AccountStore,
	AccountTypeFilter,
	BudgetStore,
	ShortAccountTypeProperty,
)
from lampyrid.models.lampyrid_models import (
	Account,
	Budget,
	DeleteTransactionRequest,
	ListBudgetsRequest,
)

# Load test environment variables FIRST, before importing settings
test_env_path = Path(__file__).parent / '.env.test'
if test_env_path.exists():
	load_dotenv(test_env_path)
else:
	# Try to load from .env.test.example for CI
	print(
		'Warning: .env.test not found. Make sure FIREFLY_BASE_URL and FIREFLY_TOKEN '
		'are set in environment.'
	)

from lampyrid.clients.firefly import FireflyClient
from lampyrid.config import settings

# Global cache for test data created programmatically
_cached_test_accounts: List[Account] | None = None
_cached_test_budgets: List[Budget] | None = None
_created_account_ids: List[str] = []  # Track created accounts for cleanup
_created_budget_ids: List[str] = []  # Track created budgets for cleanup


@pytest.fixture(scope='function')
async def event_loop():
	"""Create an event loop for the test session that won't be closed prematurely."""
	loop = asyncio.new_event_loop()
	yield loop
	# Don't close the loop here - let pytest-asyncio handle it
	try:
		loop.close()
	except RuntimeError:
		pass  # Loop already closed


@pytest.fixture(scope='session', autouse=True)
async def _setup_test_data():
	"""
	Autouse fixture to create test accounts and budget at session start.
	This ensures test data exists before any tests run.
	"""

	global _cached_test_accounts, _cached_test_budgets

	test_env_path = Path(__file__).parent / '.env.test'
	if test_env_path.exists():
		load_dotenv(test_env_path)

	if not settings.firefly_base_url or not settings.firefly_token:
		return  # Skip setup if no config

	client = FireflyClient()

	base = str(settings.firefly_base_url).rstrip('/')
	client._client = httpx.AsyncClient(
		base_url=base,
		headers={
			'Authorization': f'Bearer {settings.firefly_token}',
			'Accept': 'application/json',
			'Content-Type': 'application/json',
		},
		timeout=30.0,
		limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
	)

	try:
		# Create test accounts
		if _cached_test_accounts is None or len(_cached_test_accounts) < 2:
			_cached_test_accounts = []

			account_array = await client.list_accounts(page=1, type=AccountTypeFilter.asset)
			existing_accounts = [
				Account.from_account_read(account_read) for account_read in account_array.data
			]

			checking = None
			savings = None
			for account in existing_accounts:
				if 'test checking' in account.name.lower():
					checking = account
				elif 'test savings' in account.name.lower():
					savings = account

			if checking is None:
				checking_store = AccountStore(
					name='Test Checking',
					type=ShortAccountTypeProperty.asset,
					account_role=AccountRoleProperty(AccountRolePropertyEnum.defaultAsset),
					currency_code='USD',
					opening_balance='1000.00',
					opening_balance_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
				)
				checking = await client.create_account(checking_store)
				_created_account_ids.append(checking.id)

			_cached_test_accounts.append(checking)

			if savings is None:
				savings_store = AccountStore(
					name='Test Savings',
					type=ShortAccountTypeProperty.asset,
					account_role=AccountRoleProperty(AccountRolePropertyEnum.savingAsset),
					currency_code='USD',
					opening_balance='500.00',
					opening_balance_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
				)
				savings = await client.create_account(savings_store)
				_created_account_ids.append(savings.id)

			_cached_test_accounts.append(savings)

		# Create test budget
		if _cached_test_budgets is None:
			_cached_test_budgets = []

			budget_array = await client.list_budgets(ListBudgetsRequest(active=True))
			existing_budgets = [
				Budget.from_budget_read(budget_read) for budget_read in budget_array.data
			]

			test_budget = None
			for budget in existing_budgets:
				if 'test budget' in budget.name.lower():
					test_budget = budget
					break

			if test_budget is None:
				budget_store = BudgetStore(name='Test Budget', active=True)
				test_budget = await client.create_budget(budget_store)
				_created_budget_ids.append(test_budget.id)

			_cached_test_budgets.append(test_budget)

	finally:
		await client._client.aclose()


@pytest.fixture(scope='function')
async def firefly_client():
	"""
	Create a FireflyClient instance for testing.

	This fixture is function-scoped to avoid event loop conflicts.
	The client reads configuration from the global settings object which
	loads from environment variables (.env.test file).
	"""

	# Validate that required settings are present
	if not settings.firefly_base_url or not settings.firefly_token:
		raise RuntimeError(
			'FIREFLY_BASE_URL and FIREFLY_TOKEN must be set in environment or .env.test file'
		)

	client = FireflyClient()

	# Override the httpx client with connection limits to prevent pooling issues
	base = str(settings.firefly_base_url).rstrip('/')
	client._client = httpx.AsyncClient(
		base_url=base,
		headers={
			'Authorization': f'Bearer {settings.firefly_token}',
			'Accept': 'application/json',
			'Content-Type': 'application/json',
		},
		timeout=30.0,
		limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
	)

	yield client

	# Explicitly close the client to clean up connections
	try:
		await client._client.aclose()
	except Exception:
		pass  # Ignore errors during cleanup


@pytest.fixture(scope='session')
def test_asset_account() -> Account:
	"""
	Get the first test asset account (Test Checking).
	The account is created by the autouse _setup_test_data fixture.
	"""
	if _cached_test_accounts is None or len(_cached_test_accounts) == 0:
		raise RuntimeError('Test accounts not initialized. Check if _setup_test_data ran.')
	return _cached_test_accounts[0]


@pytest.fixture(scope='session')
def test_second_asset_account() -> Account:
	"""
	Get the second test asset account (Test Savings) for transfer testing.
	The account is created by the autouse _setup_test_data fixture.
	"""
	if _cached_test_accounts is None or len(_cached_test_accounts) < 2:
		raise RuntimeError('Test accounts not initialized. Check if _setup_test_data ran.')
	return _cached_test_accounts[1]


@pytest.fixture(scope='session')
def test_expense_account() -> str:
	"""
	Get expense account name for withdrawal testing.
	For withdrawals, we only need the destination name (expense account),
	not the full account object.
	"""
	# Return a default name - Firefly III will create it automatically
	return 'Test Expense'


@pytest.fixture(scope='session')
def test_revenue_account() -> str:
	"""
	Get revenue account name for deposit testing.
	For deposits, we only need the source name (revenue account),
	not the full account object.
	"""
	# Return a default name - Firefly III will create it automatically
	return 'Test Revenue'


@pytest.fixture(scope='session')
def test_budget() -> Budget:
	"""
	Get the test budget.
	The budget is created by the autouse _setup_test_data fixture.
	"""
	if _cached_test_budgets is None or len(_cached_test_budgets) == 0:
		raise RuntimeError('Test budget not initialized. Check if _setup_test_data ran.')
	return _cached_test_budgets[0]


@pytest.fixture
async def transaction_cleanup(firefly_client: FireflyClient):
	"""
	Fixture to track and cleanup transactions created during tests.

	Usage:
		@pytest.mark.asyncio
		async def test_create_transaction(firefly_client, transaction_cleanup):
			transaction = await create_transaction(...)
			transaction_cleanup.append(transaction.id)
			# Test code here
			# Transaction will be deleted after test completes
	"""
	created_transaction_ids: List[str] = []

	# Provide the list to the test
	yield created_transaction_ids

	# Cleanup after test

	for transaction_id in created_transaction_ids:
		try:
			await firefly_client.delete_transaction(DeleteTransactionRequest(id=transaction_id))
			print(f'Cleaned up transaction: {transaction_id}')
		except Exception as e:
			print(f'Failed to cleanup transaction {transaction_id}: {e}')
