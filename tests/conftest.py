"""
Test configuration and shared fixtures for LamPyrid integration tests.

This module provides pytest fixtures for:
- FireflyClient instance configured for testing
- Test accounts (asset, expense, revenue)
- Test budgets
- Transaction cleanup utilities
"""

import asyncio
from pathlib import Path
from typing import List

import pytest
from dotenv import load_dotenv

from lampyrid.clients.firefly import FireflyClient
from lampyrid.config import settings
from lampyrid.models.firefly_models import AccountTypeFilter
from lampyrid.models.lampyrid_models import Account, Budget

# Load test environment variables
test_env_path = Path(__file__).parent / '.env.test'
if test_env_path.exists():
	load_dotenv(test_env_path)
else:
	# Try to load from .env.test.example for CI
	print(
		'Warning: .env.test not found. Make sure FIREFLY_BASE_URL and FIREFLY_TOKEN '
		'are set in environment.'
	)

# Global cache for test data created programmatically
_cached_test_accounts: List[Account] | None = None
_cached_test_budgets: List[Budget] | None = None
_created_account_ids: List[str] = []  # Track created accounts for cleanup
_created_budget_ids: List[str] = []  # Track created budgets for cleanup


@pytest.fixture(scope='function')
def event_loop():
	"""Create an event loop for the test session that won't be closed prematurely."""
	policy = asyncio.get_event_loop_policy()
	loop = policy.new_event_loop()
	yield loop
	# Don't close the loop here - let pytest-asyncio handle it
	try:
		loop.close()
	except RuntimeError:
		pass  # Loop already closed


@pytest.fixture(scope='function')
async def firefly_client():
	"""
	Create a FireflyClient instance for testing.

	This fixture is function-scoped to avoid event loop conflicts.
	The client reads configuration from the global settings object which
	loads from environment variables (.env.test file).
	"""
	import httpx

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


@pytest.fixture(scope='function')
async def test_asset_account(firefly_client: FireflyClient) -> Account:
	"""
	Create or find test asset accounts programmatically.

	Uses global cache to create only once across all tests.
	This account is used as the source for withdrawals and destination for deposits.
	"""
	from datetime import datetime, timezone

	from lampyrid.models.firefly_models import AccountStore, ShortAccountTypeProperty

	global _cached_test_accounts, _created_account_ids

	# Create and cache if not already created
	if _cached_test_accounts is None or len(_cached_test_accounts) < 2:
		_cached_test_accounts = []

		# First check if test accounts already exist
		account_array = await firefly_client.list_accounts(page=1, type=AccountTypeFilter.asset)
		existing_accounts = [
			Account.from_account_read(account_read) for account_read in account_array.data
		]

		# Look for existing test accounts
		checking = None
		savings = None
		for account in existing_accounts:
			if 'test checking' in account.name.lower():
				checking = account
				print(f'Using existing test checking account: {checking.name} (ID: {checking.id})')
			elif 'test savings' in account.name.lower():
				savings = account
				print(f'Using existing test savings account: {savings.name} (ID: {savings.id})')

		# Create checking if not found
		if checking is None:
			checking_store = AccountStore(
				name='Test Checking',
				type=ShortAccountTypeProperty.asset,
				account_role='defaultAsset',
				currency_code='USD',
				opening_balance='1000.00',
				opening_balance_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
			)
			checking = await firefly_client.create_account(checking_store)
			_created_account_ids.append(checking.id)
			print(f'Created test checking account: {checking.name} (ID: {checking.id})')

		_cached_test_accounts.append(checking)

		# Create savings if not found
		if savings is None:
			savings_store = AccountStore(
				name='Test Savings',
				type=ShortAccountTypeProperty.asset,
				account_role='savingAsset',
				currency_code='USD',
				opening_balance='500.00',
				opening_balance_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
			)
			savings = await firefly_client.create_account(savings_store)
			_created_account_ids.append(savings.id)
			print(f'Created test savings account: {savings.name} (ID: {savings.id})')

		_cached_test_accounts.append(savings)

	return _cached_test_accounts[0]


@pytest.fixture(scope='function')
async def test_second_asset_account(firefly_client: FireflyClient) -> Account:
	"""
	Get the second test asset account for transfer testing.

	Depends on test_asset_account creating both accounts.
	This account is used as the destination for transfer transactions.
	"""
	global _cached_test_accounts

	# Ensure accounts are created
	if _cached_test_accounts is None or len(_cached_test_accounts) < 2:
		# Trigger creation via test_asset_account
		await test_asset_account(firefly_client)

	# Return second account
	print(
		f'Using second asset account: {_cached_test_accounts[1].name} (ID: {_cached_test_accounts[1].id})'
	)
	return _cached_test_accounts[1]


@pytest.fixture(scope='function')
async def test_expense_account(firefly_client: FireflyClient) -> str:
	"""
	Get expense account name for withdrawal testing.

	For withdrawals, we only need the destination name (expense account),
	not the full account object.
	"""
	# Get all expense accounts
	account_array = await firefly_client.list_accounts(page=1, type=AccountTypeFilter.expense)

	# Convert to Account objects
	accounts: List[Account] = [
		Account.from_account_read(account_read) for account_read in account_array.data
	]

	# Look for test expense account
	for account in accounts:
		if 'test' in account.name.lower():
			print(f'Using test expense account: {account.name}')
			return account.name

	# Use first expense account or default name
	if accounts:
		print(f'Using expense account: {accounts[0].name}')
		return accounts[0].name

	# Return a default name - Firefly III will create it automatically
	print('Using default expense account name: Test Expense')
	return 'Test Expense'


@pytest.fixture(scope='function')
async def test_revenue_account(firefly_client: FireflyClient) -> str:
	"""
	Get revenue account name for deposit testing.

	For deposits, we only need the source name (revenue account),
	not the full account object.
	"""
	# Get all revenue accounts
	account_array = await firefly_client.list_accounts(page=1, type=AccountTypeFilter.revenue)

	# Convert to Account objects
	accounts: List[Account] = [
		Account.from_account_read(account_read) for account_read in account_array.data
	]

	# Look for test revenue account
	for account in accounts:
		if 'test' in account.name.lower():
			print(f'Using test revenue account: {account.name}')
			return account.name

	# Use first revenue account or default name
	if accounts:
		print(f'Using revenue account: {accounts[0].name}')
		return accounts[0].name

	# Return a default name - Firefly III will create it automatically
	print('Using default revenue account name: Test Revenue')
	return 'Test Revenue'


@pytest.fixture(scope='function')
async def test_budget(firefly_client: FireflyClient) -> Budget:
	"""
	Create or find a test budget programmatically.

	Uses global cache to create only once across all tests.
	This budget is used for testing budget allocation in withdrawals.
	"""
	from lampyrid.models.firefly_models import BudgetStore
	from lampyrid.models.lampyrid_models import ListBudgetsRequest

	global _cached_test_budgets, _created_budget_ids

	# Create and cache if not already created
	if _cached_test_budgets is None:
		_cached_test_budgets = []

		# First check if test budget already exists
		budget_array = await firefly_client.list_budgets(ListBudgetsRequest(active=True))
		existing_budgets = [
			Budget.from_budget_read(budget_read) for budget_read in budget_array.data
		]

		# Look for existing test budget
		test_budget = None
		for budget in existing_budgets:
			if 'test budget' in budget.name.lower():
				test_budget = budget
				print(f'Using existing test budget: {test_budget.name} (ID: {test_budget.id})')
				break

		# Create if not found
		if test_budget is None:
			budget_store = BudgetStore(name='Test Budget', active=True)
			test_budget = await firefly_client.create_budget(budget_store)
			_created_budget_ids.append(test_budget.id)
			print(f'Created test budget: {test_budget.name} (ID: {test_budget.id})')

		_cached_test_budgets.append(test_budget)

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
	from lampyrid.models.lampyrid_models import DeleteTransactionRequest

	for transaction_id in created_transaction_ids:
		try:
			await firefly_client.delete_transaction(DeleteTransactionRequest(id=transaction_id))
			print(f'Cleaned up transaction: {transaction_id}')
		except Exception as e:
			print(f'Failed to cleanup transaction {transaction_id}: {e}')
