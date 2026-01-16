"""Integration tests for transaction management tools."""

from datetime import datetime, timedelta
from typing import List

import pytest
from httpx import HTTPStatusError

from lampyrid.clients.firefly import FireflyClient
from lampyrid.models.firefly_models import TransactionTypeFilter, TransactionTypeProperty
from lampyrid.models.lampyrid_models import Account, Budget, Transaction
from tests.fixtures.transactions import (
	make_create_bulk_transactions_request,
	make_create_deposit_request,
	make_create_transfer_request,
	make_create_withdrawal_request,
	make_delete_transaction_request,
	make_get_transaction_request,
	make_get_transactions_request,
	make_search_transactions_request,
	make_update_transaction_request,
)

# ==================== Create Operations ====================


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_withdrawal_basic(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test creating a basic withdrawal transaction."""
	req = make_create_withdrawal_request(
		amount=10.50,
		description='Test withdrawal - coffee',
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
	)

	transaction = await firefly_client.create_withdrawal(req)
	assert transaction is not None
	assert transaction.id is not None
	transaction_cleanup.append(transaction.id)

	# Verify transaction was created
	assert transaction.amount == 10.50
	assert transaction.description == 'Test withdrawal - coffee'
	assert transaction.type.value == 'withdrawal'


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_withdrawal_with_budget(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	test_budget: Budget,
	transaction_cleanup: List[str],
):
	"""Test creating a withdrawal with budget allocation."""
	req = make_create_withdrawal_request(
		amount=25.00,
		description='Test withdrawal with budget - groceries',
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
		budget_id=test_budget.id,
	)

	transaction = await firefly_client.create_withdrawal(req)
	assert transaction is not None
	assert transaction.id is not None
	transaction_cleanup.append(transaction.id)

	# Verify transaction was created with budget
	assert transaction.budget_id == test_budget.id
	assert transaction.amount == 25.00


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_deposit_basic(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_revenue_account: str,
	transaction_cleanup: List[str],
):
	"""Test creating a basic deposit transaction."""
	req = make_create_deposit_request(
		amount=500.00,
		description='Test deposit - salary',
		destination_id=test_asset_account.id,
		source_name=test_revenue_account,
	)

	transaction = await firefly_client.create_deposit(req)
	assert transaction is not None
	assert transaction.id is not None
	transaction_cleanup.append(transaction.id)

	# Verify transaction was created
	assert transaction.amount == 500.00
	assert transaction.description == 'Test deposit - salary'
	assert transaction.type.value == 'deposit'


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_transfer_basic(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_second_asset_account: Account,
	transaction_cleanup: List[str],
):
	"""Test creating a transfer between asset accounts."""
	req = make_create_transfer_request(
		amount=100.00,
		description='Test transfer between accounts',
		source_id=test_asset_account.id,
		destination_id=test_second_asset_account.id,
	)

	transaction = await firefly_client.create_transfer(req)
	assert transaction is not None
	assert transaction.id is not None
	transaction_cleanup.append(transaction.id)

	# Verify transaction was created
	assert transaction.amount == 100.00
	assert transaction.description == 'Test transfer between accounts'
	assert transaction.type.value == 'transfer'


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_bulk_transactions(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	test_revenue_account: str,
	transaction_cleanup: List[str],
):
	"""Test creating multiple transactions in bulk."""
	from datetime import timezone

	# Create 3 transactions: 1 withdrawal, 1 deposit, 1 withdrawal
	transactions = [
		Transaction(
			amount=5.00,
			description='Bulk test - transaction 1',
			type=TransactionTypeProperty.withdrawal,
			date=datetime.now(timezone.utc),
			source_id=test_asset_account.id,
			destination_name=test_expense_account,
		),
		Transaction(
			amount=100.00,
			description='Bulk test - transaction 2',
			type=TransactionTypeProperty.deposit,
			date=datetime.now(timezone.utc),
			source_name=test_revenue_account,
			destination_id=test_asset_account.id,
		),
		Transaction(
			amount=15.00,
			description='Bulk test - transaction 3',
			type=TransactionTypeProperty.withdrawal,
			date=datetime.now(timezone.utc),
			source_id=test_asset_account.id,
			destination_name=test_expense_account,
		),
	]

	req = make_create_bulk_transactions_request(transactions=transactions)
	created = await firefly_client.create_bulk_transactions(req)

	# Add all to cleanup
	for txn in created:
		assert txn is not None
		assert txn.id is not None
		transaction_cleanup.append(txn.id)

	# Verify all transactions were created
	assert len(created) == 3
	assert created[0].description == 'Bulk test - transaction 1'
	assert created[1].description == 'Bulk test - transaction 2'
	assert created[2].description == 'Bulk test - transaction 3'


# ==================== Read Operations ====================


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_get_transaction(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test retrieving a single transaction by ID."""
	# Create a transaction first
	create_req = make_create_withdrawal_request(
		amount=7.50,
		description='Test get transaction',
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
	)
	created = await firefly_client.create_withdrawal(create_req)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Now retrieve it
	get_req = make_get_transaction_request(transaction_id=created.id)
	transaction = await firefly_client.get_transaction(get_req)

	# Verify it's the same transaction
	assert transaction.id == created.id
	assert transaction.description == 'Test get transaction'
	assert transaction.amount == 7.50


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_get_transactions_all(firefly_client: FireflyClient):
	"""Test listing all transactions without filters."""
	from lampyrid.models.lampyrid_models import TransactionListResponse

	req = make_get_transactions_request()
	transaction_array = await firefly_client.get_transactions(req)
	result = TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)

	# Should have at least some transactions (including test transactions)
	assert len(result.transactions) > 0
	assert result.total_count is not None and result.total_count > 0


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_get_transactions_filtered(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test filtering transactions by date range and type."""
	from datetime import timezone

	# Create a transaction first
	create_req = make_create_withdrawal_request(
		amount=12.00,
		description='Test filtered transaction',
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
		date=datetime.now(timezone.utc),
	)
	created = await firefly_client.create_withdrawal(create_req)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Get transactions from last 7 days, withdrawals only
	from lampyrid.models.lampyrid_models import TransactionListResponse

	end_date = datetime.now(timezone.utc).date()
	start_date = (datetime.now(timezone.utc) - timedelta(days=7)).date()

	req = make_get_transactions_request(
		start_date=start_date,
		end_date=end_date,
		transaction_type=TransactionTypeFilter.withdrawal,
	)
	transaction_array = await firefly_client.get_transactions(req)
	result = TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)

	# Should include our test transaction
	transaction_ids = [t.id for t in result.transactions]
	assert created.id in transaction_ids


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_get_transactions_paginated(firefly_client: FireflyClient):
	"""Test pagination of transaction results."""
	from lampyrid.models.lampyrid_models import TransactionListResponse

	# Get first page with limit of 5
	req = make_get_transactions_request(page=1, limit=5)
	transaction_array = await firefly_client.get_transactions(req)
	result = TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)

	# Should respect limit
	assert len(result.transactions) <= 5
	assert result.current_page == 1
	assert result.per_page == 5


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_search_transactions_description(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test searching transactions by description."""
	from datetime import timezone

	# Create a transaction with unique description
	unique_desc = f'Unique search test {datetime.now(timezone.utc).timestamp()}'
	create_req = make_create_withdrawal_request(
		amount=3.00,
		description=unique_desc,
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
	)
	created = await firefly_client.create_withdrawal(create_req)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Search by description
	from lampyrid.models.lampyrid_models import TransactionListResponse

	search_req = make_search_transactions_request(description_contains=unique_desc)
	transaction_array = await firefly_client.search_transactions(search_req)
	result = TransactionListResponse.from_transaction_array(
		transaction_array, current_page=search_req.page or 1, per_page=search_req.limit or 50
	)

	# Should find our transaction
	assert len(result.transactions) > 0
	transaction_ids = [t.id for t in result.transactions]
	assert created.id in transaction_ids


# ==================== Update Operations ====================


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_update_transaction_amount(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test updating transaction amount."""
	# Create a transaction
	create_req = make_create_withdrawal_request(
		amount=10.00,
		description='Test update amount',
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
	)
	created = await firefly_client.create_withdrawal(create_req)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Update the amount
	update_req = make_update_transaction_request(transaction_id=created.id, amount=15.00)
	updated = await firefly_client.update_transaction(update_req)

	# Verify amount was updated
	assert updated.id == created.id
	assert updated.amount == 15.00


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_update_transaction_description(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test updating transaction description."""
	# Create a transaction
	create_req = make_create_withdrawal_request(
		amount=8.00,
		description='Old description',
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
	)
	created = await firefly_client.create_withdrawal(create_req)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Update the description
	update_req = make_update_transaction_request(
		transaction_id=created.id, description='New description'
	)
	updated = await firefly_client.update_transaction(update_req)

	# Verify description was updated
	assert updated.id == created.id
	assert updated.description == 'New description'


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_update_transaction_budget(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
	test_budget: Budget,
	transaction_cleanup: List[str],
):
	"""Test updating transaction budget allocation."""
	# Create a transaction without budget
	create_req = make_create_withdrawal_request(
		amount=20.00,
		description='Test update budget',
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
	)
	created = await firefly_client.create_withdrawal(create_req)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Update to add budget
	update_req = make_update_transaction_request(
		transaction_id=created.id, budget_id=test_budget.id
	)
	updated = await firefly_client.update_transaction(update_req)

	# Verify budget was added
	assert updated.id == created.id
	assert updated.budget_id == test_budget.id


# ==================== Delete Operations ====================


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_delete_transaction(
	firefly_client: FireflyClient,
	test_asset_account: Account,
	test_expense_account: str,
):
	"""Test deleting a transaction."""
	# Create a transaction
	create_req = make_create_withdrawal_request(
		amount=1.00,
		description='Test delete',
		source_id=test_asset_account.id,
		destination_name=test_expense_account,
	)
	created = await firefly_client.create_withdrawal(create_req)
	assert created is not None
	assert created.id is not None

	# Delete it
	delete_req = make_delete_transaction_request(transaction_id=created.id)
	result = await firefly_client.delete_transaction(delete_req)

	# Should return True
	assert result is True

	# Verify it was deleted by trying to get it
	get_req = make_get_transaction_request(transaction_id=created.id)
	with pytest.raises(HTTPStatusError) as exc_info:
		await firefly_client.get_transaction(get_req)

	assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_delete_nonexistent_transaction(firefly_client: FireflyClient):
	"""Test handling deletion of non-existent transaction (404)."""
	delete_req = make_delete_transaction_request(transaction_id='999999')

	# Should raise HTTPStatusError with 404
	with pytest.raises(HTTPStatusError) as exc_info:
		await firefly_client.delete_transaction(delete_req)

	assert exc_info.value.response.status_code == 404
