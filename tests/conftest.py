"""Test configuration and shared fixtures for LamPyrid integration tests.

This module provides pytest fixtures for:
- FireflyClient instance configured for testing
- Test accounts (asset, expense, revenue)
- Test budgets
- Transaction cleanup utilities
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pytest
from dotenv import load_dotenv
from fastmcp import Client, FastMCP

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
    ListAccountRequest,
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


from lampyrid.clients.firefly import FireflyClient  # noqa: E402
from lampyrid.config import settings  # noqa: E402
from lampyrid.services import AccountService, BudgetService  # noqa: E402
from lampyrid.tools import compose_all_servers  # noqa: E402

# Global cache for test data created programmatically
_cached_test_accounts: List[Account] | None = None
_cached_test_budgets: List[Budget] | None = None
_created_account_ids: List[str] = []  # Track created accounts for cleanup
_created_budget_ids: List[str] = []  # Track created budgets for cleanup


@pytest.fixture(scope='session', autouse=True)
async def _setup_test_data():
    """Autouse fixture to create test accounts and budget at session start.

    This ensures test data exists before any tests run.
    """
    global _cached_test_accounts, _cached_test_budgets

    test_env_path = Path(__file__).parent / '.env.test'
    if test_env_path.exists():
        load_dotenv(test_env_path)

    if not settings.firefly_base_url or not settings.firefly_token:
        return  # Skip setup if no config

    client = FireflyClient()
    account_service = AccountService(client)
    budget_service = BudgetService(client)

    try:
        # Create test accounts
        if _cached_test_accounts is None or len(_cached_test_accounts) < 2:
            _cached_test_accounts = []

            existing_accounts = await account_service.list_accounts(
                ListAccountRequest(type=AccountTypeFilter.asset)
            )

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
                checking = await account_service.create_account(checking_store)
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
                savings = await account_service.create_account(savings_store)
                _created_account_ids.append(savings.id)

            _cached_test_accounts.append(savings)

            # Create expense account for withdrawal tests
            existing_expense = await account_service.list_accounts(
                ListAccountRequest(type=AccountTypeFilter.expense)
            )

            expense = None
            for account in existing_expense:
                if 'test expense' in account.name.lower():
                    expense = account
                    break

            if expense is None:
                expense_store = AccountStore(
                    name='Test Expense',
                    type=ShortAccountTypeProperty.expense,
                    currency_code='EUR',
                )
                expense = await account_service.create_account(expense_store)
                _created_account_ids.append(expense.id)

            _cached_test_accounts.append(expense)

            # Create revenue account for deposit tests
            existing_revenue = await account_service.list_accounts(
                ListAccountRequest(type=AccountTypeFilter.revenue)
            )

            revenue = None
            for account in existing_revenue:
                if 'test revenue' in account.name.lower():
                    revenue = account
                    break

            if revenue is None:
                revenue_store = AccountStore(
                    name='Test Revenue',
                    type=ShortAccountTypeProperty.revenue,
                    currency_code='EUR',
                )
                revenue = await account_service.create_account(revenue_store)
                _created_account_ids.append(revenue.id)

            _cached_test_accounts.append(revenue)

        # Create test budget
        if _cached_test_budgets is None:
            _cached_test_budgets = []

            budget_array = await budget_service.list_budgets(ListBudgetsRequest(active=True))

            test_budget = None
            for budget in budget_array:
                if 'test budget' in budget.name.lower():
                    test_budget = budget
                    break

            if test_budget is None:
                budget_store = BudgetStore(name='Test Budget', active=True)
                test_budget = await budget_service.create_budget(budget_store)
                _created_budget_ids.append(test_budget.id)

            _cached_test_budgets.append(test_budget)

    finally:
        await client._client.aclose()


@pytest.fixture(scope='function')
async def firefly_client():
    """Create a FireflyClient instance for testing.

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

    yield client

    # Explicitly close the client to clean up connections
    try:
        await client._client.aclose()
    except Exception:
        pass  # Ignore errors during cleanup


@pytest.fixture(scope='function')
async def mcp_client(firefly_client: FireflyClient):
    """Create a FastMCP Client for testing tools.

    This fixture uses in-memory transport to test the full MCP stack:
    MCP Protocol -> Tool Functions -> FireflyClient -> Firefly III API

    The server is created fresh for each test function to ensure isolation.
    All domain-specific tools (accounts, transactions, budgets) are composed
    into the server.
    """
    # Create a new FastMCP server for testing
    mcp = FastMCP('lampyrid-test')

    # Compose all domain servers (accounts, transactions, budgets)
    await compose_all_servers(mcp, firefly_client)

    # Create a FastMCP Client using in-memory transport
    async with Client(transport=mcp) as client:
        yield client


@pytest.fixture(scope='session')
def test_asset_account() -> Account:
    """Get the first test asset account (Test Checking).

    The account is created by the autouse _setup_test_data fixture.
    """
    if _cached_test_accounts is None or len(_cached_test_accounts) == 0:
        raise RuntimeError('Test accounts not initialized. Check if _setup_test_data ran.')
    return _cached_test_accounts[0]


@pytest.fixture(scope='session')
def test_second_asset_account() -> Account:
    """Get the second test asset account (Test Savings) for transfer testing.

    The account is created by the autouse _setup_test_data fixture.
    """
    if _cached_test_accounts is None or len(_cached_test_accounts) < 2:
        raise RuntimeError('Test accounts not initialized. Check if _setup_test_data ran.')
    return _cached_test_accounts[1]


@pytest.fixture(scope='session')
def test_expense_account() -> str:
    """Get expense account name for withdrawal testing.

    For withdrawals, we only need the destination name (expense account),
    not the full account object.
    """
    # Return a default name - Firefly III will create it automatically
    return 'Test Expense'


@pytest.fixture(scope='session')
def test_revenue_account() -> str:
    """Get revenue account name for deposit testing.

    For deposits, we only need the source name (revenue account),
    not the full account object.
    """
    # Return a default name - Firefly III will create it automatically
    return 'Test Revenue'


@pytest.fixture(scope='session')
def test_budget() -> Budget:
    """Get the test budget.

    The budget is created by the autouse _setup_test_data fixture.
    """
    if _cached_test_budgets is None or len(_cached_test_budgets) == 0:
        raise RuntimeError('Test budget not initialized. Check if _setup_test_data ran.')
    return _cached_test_budgets[0]


@pytest.fixture
async def transaction_cleanup(firefly_client: FireflyClient):
    """Fixture to track and cleanup transactions created during tests.

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
            await firefly_client.delete_transaction(transaction_id)
            print(f'Cleaned up transaction: {transaction_id}')
        except Exception as e:
            print(f'Failed to cleanup transaction {transaction_id}: {e}')
