"""Integration tests for account management tools."""

import pytest
from httpx import HTTPStatusError

from lampyrid.clients.firefly import FireflyClient
from lampyrid.models.firefly_models import AccountTypeFilter
from lampyrid.models.lampyrid_models import Account
from tests.fixtures.accounts import (
	make_get_account_request,
	make_list_account_request,
	make_search_account_request,
)


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_list_accounts_all(firefly_client: FireflyClient):
	"""Test listing all account types."""
	req = make_list_account_request(AccountTypeFilter.all)
	account_array = await firefly_client.list_accounts(page=1, type=req.type)

	# Convert to Account objects
	accounts = [Account.from_account_read(account_read) for account_read in account_array.data]

	# Should have at least one account
	assert len(accounts) > 0

	# All accounts should have required fields
	for account in accounts:
		assert account.id is not None
		assert account.name is not None
		assert account.type is not None


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_list_accounts_by_type_asset(firefly_client: FireflyClient):
	"""Test filtering accounts by asset type."""
	req = make_list_account_request(AccountTypeFilter.asset)
	account_array = await firefly_client.list_accounts(page=1, type=req.type)

	# Convert to Account objects
	accounts = [Account.from_account_read(account_read) for account_read in account_array.data]

	# Should have at least one asset account for tests to work
	assert len(accounts) > 0

	# All accounts should be asset type
	for account in accounts:
		assert account.type.value == 'asset'


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_list_accounts_by_type_expense(firefly_client: FireflyClient):
	"""Test filtering accounts by expense type."""
	req = make_list_account_request(type=AccountTypeFilter.expense)
	account_array = await firefly_client.list_accounts(page=1, type=req.type)

	# Convert to Account objects
	accounts = [Account.from_account_read(account_read) for account_read in account_array.data]

	# May or may not have expense accounts
	# If we have any, they should all be expense type
	for account in accounts:
		assert account.type.value == 'expense'


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_list_accounts_by_type_revenue(firefly_client: FireflyClient):
	"""Test filtering accounts by revenue type."""
	req = make_list_account_request(type=AccountTypeFilter.revenue)
	account_array = await firefly_client.list_accounts(page=1, type=req.type)

	# Convert to Account objects
	accounts = [Account.from_account_read(account_read) for account_read in account_array.data]

	# May or may not have revenue accounts
	# If we have any, they should all be revenue type
	for account in accounts:
		assert account.type.value == 'revenue'


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_get_account_valid(firefly_client: FireflyClient, test_asset_account: Account):
	"""Test retrieving a single account by valid ID."""
	req = make_get_account_request(account_id=test_asset_account.id)
	account = await firefly_client.get_account(req)

	# Should return the same account
	assert account.id == test_asset_account.id
	assert account.name == test_asset_account.name
	assert account.type == test_asset_account.type


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_get_account_invalid(firefly_client: FireflyClient):
	"""Test handling of invalid account ID (404)."""
	req = make_get_account_request(account_id='999999')

	# Should raise HTTPStatusError with 404
	with pytest.raises(HTTPStatusError) as exc_info:
		await firefly_client.get_account(req)

	assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_search_accounts_exact(firefly_client: FireflyClient, test_asset_account: Account):
	"""Test searching accounts with exact name match."""
	req = make_search_account_request(query=test_asset_account.name)
	account_array = await firefly_client.search_accounts(req)

	# Convert to Account objects
	accounts = [Account.from_account_read(account_read) for account_read in account_array.data]

	# Should find at least the test account
	assert len(accounts) > 0

	# Should contain our test account
	account_ids = [account.id for account in accounts]
	assert test_asset_account.id in account_ids


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_search_accounts_partial(firefly_client: FireflyClient, test_asset_account: Account):
	"""Test searching accounts with partial name matching."""
	# Use first 3 characters of account name
	partial_name = test_asset_account.name[:3]
	req = make_search_account_request(query=partial_name)
	account_array = await firefly_client.search_accounts(req)

	# Convert to Account objects
	accounts = [Account.from_account_read(account_read) for account_read in account_array.data]

	# Should find at least one account
	assert len(accounts) > 0

	# Should contain our test account (or at least accounts starting with the partial name)
	account_ids = [account.id for account in accounts]
	assert test_asset_account.id in account_ids


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_search_accounts_with_type(
	firefly_client: FireflyClient, test_asset_account: Account
):
	"""Test searching accounts with type filtering."""
	req = make_search_account_request(query=test_asset_account.name, type=AccountTypeFilter.asset)
	account_array = await firefly_client.search_accounts(req)

	# Convert to Account objects
	accounts = [Account.from_account_read(account_read) for account_read in account_array.data]

	# Should find at least the test account
	assert len(accounts) > 0

	# All results should be asset type
	for account in accounts:
		assert account.type.value == 'asset'

	# Should contain our test account
	account_ids = [account.id for account in accounts]
	assert test_asset_account.id in account_ids


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_search_accounts_no_results(firefly_client: FireflyClient):
	"""Test searching accounts with no matching results."""
	# Use a query that should not match any account
	req = make_search_account_request(query='xyzabc123nonexistent')
	account_array = await firefly_client.search_accounts(req)

	# Convert to Account objects
	accounts = [Account.from_account_read(account_read) for account_read in account_array.data]

	# Should return empty list
	assert len(accounts) == 0
