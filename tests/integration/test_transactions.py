"""Integration tests for transaction management tools."""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest
from dirty_equals import IsDatetime, IsStr
from fastmcp import Client
from fastmcp.exceptions import ToolError
from inline_snapshot import snapshot

from lampyrid.models.lampyrid_models import Account, Budget, Transaction, TransactionListResponse

# ==================== Create Operations ====================


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_withdrawal_basic(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test creating a basic withdrawal transaction."""
	result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 10.50,
				'description': 'Test withdrawal - coffee',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	transaction = Transaction.model_validate(result.structured_content)
	assert transaction is not None
	assert transaction.id is not None
	transaction_cleanup.append(transaction.id)

	# Validate transaction structure with snapshot
	assert result.structured_content == snapshot(
		{
			'id': IsStr(min_length=1),
			'amount': 10.5,
			'description': 'Test withdrawal - coffee',
			'type': 'withdrawal',
			'date': IsDatetime(iso_string=True),
			'source_id': '1',
			'destination_id': '5',
			'source_name': 'Test Checking',
			'destination_name': 'Test Expense',
			'currency_code': 'USD',
			'budget_id': None,
			'budget_name': None,
		}
	)


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_withdrawal_with_budget(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	test_budget: Budget,
	transaction_cleanup: List[str],
):
	"""Test creating a withdrawal with budget allocation."""
	result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 25.00,
				'description': 'Test withdrawal with budget - groceries',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'budget_id': test_budget.id,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	transaction = Transaction.model_validate(result.structured_content)
	assert transaction is not None
	assert transaction.id is not None
	transaction_cleanup.append(transaction.id)

	# Verify transaction was created with budget
	assert result.structured_content == snapshot(
		{
			'id': IsStr(min_length=1),
			'amount': 25.0,
			'description': 'Test withdrawal with budget - groceries',
			'type': 'withdrawal',
			'date': IsDatetime(iso_string=True),
			'source_id': '1',
			'destination_id': '5',
			'source_name': 'Test Checking',
			'destination_name': 'Test Expense',
			'currency_code': 'USD',
			'budget_id': '1',
			'budget_name': 'Test Budget',
		}
	)


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_deposit_basic(
	mcp_client: Client,
	test_asset_account: Account,
	test_revenue_account: str,
	transaction_cleanup: List[str],
):
	"""Test creating a basic deposit transaction."""
	result = await mcp_client.call_tool(
		'create_deposit',
		{
			'req': {
				'amount': 500.00,
				'description': 'Test deposit - salary',
				'destination_id': test_asset_account.id,
				'source_name': test_revenue_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	transaction = Transaction.model_validate(result.structured_content)
	assert transaction is not None
	assert transaction.id is not None
	transaction_cleanup.append(transaction.id)

	# Verify transaction was created
	assert result.structured_content == snapshot(
		{
			'id': IsStr(min_length=1),
			'amount': 500.0,
			'description': 'Test deposit - salary',
			'type': 'deposit',
			'date': IsDatetime(iso_string=True),
			'source_id': '6',
			'destination_id': '1',
			'source_name': 'Test Revenue',
			'destination_name': 'Test Checking',
			'currency_code': 'USD',
			'budget_id': None,
			'budget_name': None,
		}
	)


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_transfer_basic(
	mcp_client: Client,
	test_asset_account: Account,
	test_second_asset_account: Account,
	transaction_cleanup: List[str],
):
	"""Test creating a transfer between asset accounts."""
	result = await mcp_client.call_tool(
		'create_transfer',
		{
			'req': {
				'amount': 100.00,
				'description': 'Test transfer between accounts',
				'source_id': test_asset_account.id,
				'destination_id': test_second_asset_account.id,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	transaction = Transaction.model_validate(result.structured_content)
	assert transaction is not None
	assert transaction.id is not None
	transaction_cleanup.append(transaction.id)

	# Verify transaction was created
	assert result.structured_content == snapshot(
		{
			'id': IsStr(min_length=1),
			'amount': 100.0,
			'description': 'Test transfer between accounts',
			'type': 'transfer',
			'date': IsDatetime(iso_string=True),
			'source_id': '1',
			'destination_id': '3',
			'source_name': 'Test Checking',
			'destination_name': 'Test Savings',
			'currency_code': 'USD',
			'budget_id': None,
			'budget_name': None,
		}
	)


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_create_bulk_transactions(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	test_revenue_account: str,
	transaction_cleanup: List[str],
):
	"""Test creating multiple transactions in bulk."""
	# Create 3 transactions: 1 withdrawal, 1 deposit, 1 withdrawal
	transactions = [
		{
			'amount': 5.00,
			'description': 'Bulk test - transaction 1',
			'type': 'withdrawal',
			'date': datetime.now(timezone.utc).isoformat(),
			'source_id': test_asset_account.id,
			'destination_name': test_expense_account,
		},
		{
			'amount': 100.00,
			'description': 'Bulk test - transaction 2',
			'type': 'deposit',
			'date': datetime.now(timezone.utc).isoformat(),
			'source_name': test_revenue_account,
			'destination_id': test_asset_account.id,
		},
		{
			'amount': 15.00,
			'description': 'Bulk test - transaction 3',
			'type': 'withdrawal',
			'date': datetime.now(timezone.utc).isoformat(),
			'source_id': test_asset_account.id,
			'destination_name': test_expense_account,
		},
	]

	result = await mcp_client.call_tool(
		'create_bulk_transactions', {'req': {'transactions': transactions}}
	)
	created = result.data

	# Add all to cleanup
	for txn in created:
		assert txn is not None
		assert txn['id'] is not None
		transaction_cleanup.append(txn['id'])

	# Verify all transactions were created
	assert len(created) == 3
	assert created[0] == snapshot(
		{
			'id': IsStr(min_length=1),
			'amount': 5.0,
			'description': 'Bulk test - transaction 1',
			'type': 'withdrawal',
			'date': IsDatetime(iso_string=True),
			'source_id': '1',
			'destination_id': '5',
			'source_name': 'Test Checking',
			'destination_name': 'Test Expense',
			'currency_code': 'USD',
			'budget_id': None,
			'budget_name': None,
		}
	)
	assert created[1] == snapshot(
		{
			'id': IsStr(min_length=1),
			'amount': 100.0,
			'description': 'Bulk test - transaction 2',
			'type': 'deposit',
			'date': IsDatetime(iso_string=True),
			'source_id': '6',
			'destination_id': '1',
			'source_name': 'Test Revenue',
			'destination_name': 'Test Checking',
			'currency_code': 'USD',
			'budget_id': None,
			'budget_name': None,
		}
	)
	assert created[2] == snapshot(
		{
			'id': IsStr(min_length=1),
			'amount': 15.0,
			'description': 'Bulk test - transaction 3',
			'type': 'withdrawal',
			'date': IsDatetime(iso_string=True),
			'source_id': '1',
			'destination_id': '5',
			'source_name': 'Test Checking',
			'destination_name': 'Test Expense',
			'currency_code': 'USD',
			'budget_id': None,
			'budget_name': None,
		}
	)


# ==================== Read Operations ====================


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_get_transaction(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test retrieving a single transaction by ID."""
	# Create a transaction first
	create_result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 7.50,
				'description': 'Test get transaction',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	created = Transaction.model_validate(create_result.structured_content)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Now retrieve it
	get_result = await mcp_client.call_tool('get_transaction', {'req': {'id': created.id}})
	transaction = Transaction.model_validate(get_result.structured_content)

	# Verify it's the same transaction
	assert transaction.id == created.id
	assert transaction.description == 'Test get transaction'
	assert transaction.amount == 7.50

	# Validate transaction structure with snapshot
	assert get_result.structured_content == snapshot(
		{
			'id': IsStr(min_length=1),
			'amount': 7.5,
			'description': 'Test get transaction',
			'type': 'withdrawal',
			'date': IsDatetime(iso_string=True),
			'source_id': '1',
			'destination_id': '5',
			'source_name': 'Test Checking',
			'destination_name': 'Test Expense',
			'currency_code': 'USD',
			'budget_id': None,
			'budget_name': None,
		}
	)


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_get_transactions_all(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test listing all transactions without filters."""
	# Create a transaction first
	create_result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 5.00,
				'description': 'Test get all transactions',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	created = Transaction.model_validate(create_result.structured_content)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	result = await mcp_client.call_tool('get_transactions', {'req': {}})
	transactions_response = TransactionListResponse.model_validate(result.structured_content)

	# Should have at least one transaction (the one we just created)
	assert len(transactions_response.transactions) > 0
	assert transactions_response.total_count is not None and transactions_response.total_count > 0


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_get_transactions_filtered(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test filtering transactions by date range and type."""
	# Create a transaction first
	create_result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 12.00,
				'description': 'Test filtered transaction',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	created = Transaction.model_validate(create_result.structured_content)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Get transactions from last 7 days, withdrawals only
	end_date = datetime.now(timezone.utc).date()
	start_date = (datetime.now(timezone.utc) - timedelta(days=7)).date()

	result = await mcp_client.call_tool(
		'get_transactions',
		{
			'req': {
				'start_date': start_date.isoformat(),
				'end_date': end_date.isoformat(),
				'transaction_type': 'withdrawal',
			}
		},
	)
	transactions_response = TransactionListResponse.model_validate(result.structured_content)

	# Should include our test transaction
	transaction_ids = [t.id for t in transactions_response.transactions]
	assert created.id in transaction_ids


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_get_transactions_paginated(mcp_client: Client):
	"""Test pagination of transaction results."""
	# Get first page with limit of 5
	result = await mcp_client.call_tool('get_transactions', {'req': {'page': 1, 'limit': 5}})
	transactions_response = TransactionListResponse.model_validate(result.structured_content)

	# Should respect limit
	assert len(transactions_response.transactions) <= 5
	assert transactions_response.current_page == 1
	assert transactions_response.per_page == 5


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_search_transactions_description(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test searching transactions by description."""
	# Create a transaction with unique description
	unique_desc = f'Unique search test {datetime.now(timezone.utc).timestamp()}'
	create_result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 3.00,
				'description': unique_desc,
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	created = Transaction.model_validate(create_result.structured_content)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Search by description
	search_result = await mcp_client.call_tool(
		'search_transactions', {'req': {'description_contains': unique_desc}}
	)
	search_response = TransactionListResponse.model_validate(search_result.structured_content)

	# Should find our transaction
	assert len(search_response.transactions) > 0
	transaction_ids = [t.id for t in search_response.transactions]
	assert created.id in transaction_ids


# ==================== Update Operations ====================


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_update_transaction_amount(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test updating transaction amount."""
	# Create a transaction
	create_result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 10.00,
				'description': 'Test update amount',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	created = Transaction.model_validate(create_result.structured_content)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Update amount
	update_result = await mcp_client.call_tool(
		'update_transaction', {'req': {'transaction_id': created.id, 'amount': 15.00}}
	)
	updated = Transaction.model_validate(update_result.structured_content)

	# Verify amount was updated
	assert updated.id == created.id
	assert updated.amount == 15.00


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_update_transaction_description(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	transaction_cleanup: List[str],
):
	"""Test updating transaction description."""
	# Create a transaction
	create_result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 8.00,
				'description': 'Old description',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	created = Transaction.model_validate(create_result.structured_content)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Update description
	update_result = await mcp_client.call_tool(
		'update_transaction',
		{'req': {'transaction_id': created.id, 'description': 'New description'}},
	)
	updated = Transaction.model_validate(update_result.structured_content)

	# Verify description was updated
	assert updated.id == created.id
	assert updated.description == 'New description'


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_update_transaction_budget(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
	test_budget: Budget,
	transaction_cleanup: List[str],
):
	"""Test updating transaction budget allocation."""
	# Create a transaction without budget
	create_result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 20.00,
				'description': 'Test update budget',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	created = Transaction.model_validate(create_result.structured_content)
	assert created is not None
	assert created.id is not None
	transaction_cleanup.append(created.id)

	# Update to add budget
	update_result = await mcp_client.call_tool(
		'update_transaction',
		{'req': {'transaction_id': created.id, 'budget_id': test_budget.id}},
	)
	updated = Transaction.model_validate(update_result.structured_content)

	# Verify budget was added
	assert updated.id == created.id
	assert updated.budget_id == test_budget.id


# ==================== Delete Operations ====================


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_delete_transaction(
	mcp_client: Client,
	test_asset_account: Account,
	test_expense_account: str,
):
	"""Test deleting a transaction."""
	# Create a transaction
	create_result = await mcp_client.call_tool(
		'create_withdrawal',
		{
			'req': {
				'amount': 1.00,
				'description': 'Test delete',
				'source_id': test_asset_account.id,
				'destination_name': test_expense_account,
				'date': datetime.now(timezone.utc).isoformat(),
			}
		},
	)
	created = Transaction.model_validate(create_result.structured_content)
	assert created is not None
	assert created.id is not None

	# Delete it
	delete_result = await mcp_client.call_tool('delete_transaction', {'req': {'id': created.id}})
	result: bool = delete_result.data

	# Should return True
	assert result is True

	# Verify it was deleted by trying to get it
	with pytest.raises(ToolError) as exc_info:
		await mcp_client.call_tool('get_transaction', {'req': {'id': created.id}})

	assert '404' in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.transactions
@pytest.mark.integration
async def test_delete_nonexistent_transaction(mcp_client: Client):
	"""Test handling deletion of non-existent transaction (404)."""
	# Should raise HTTPStatusError with 404
	with pytest.raises(ToolError) as exc_info:
		await mcp_client.call_tool('delete_transaction', {'req': {'id': '999999'}})

	assert '404' in str(exc_info.value)
