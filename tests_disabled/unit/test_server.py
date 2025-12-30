import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import lampyrid.server as server_module
from lampyrid.models.lampyrid_models import (
	Account,
	Budget,
	BulkUpdateTransactionsRequest,
	CreateBulkTransactionsRequest,
	ListAccountRequest,
	ListBudgetsRequest,
	SearchAccountRequest,
	CreateWithdrawalRequest,
	CreateDepositRequest,
	CreateTransferRequest,
	DeleteTransactionRequest,
	GetAccountRequest,
	GetTransactionRequest,
	GetTransactionsRequest,
	SearchTransactionsRequest,
	TransactionListResponse,
	Transaction,
	TransactionType,
	UpdateTransactionRequest,
)
from lampyrid.models.firefly_models import AccountTypeFilter, AccountArray, TransactionArray


class TestMCPTools:
	"""Test MCP server tools"""

	@pytest.mark.asyncio
	async def test_list_accounts(self, sample_account_array: AccountArray):
		"""Test list_accounts tool"""
		with patch('lampyrid.server._client') as mock_client:
			mock_client.list_accounts = AsyncMock(return_value=sample_account_array)

			request = ListAccountRequest(type=AccountTypeFilter.asset)
			# Access the underlying function from the tool
			result = await server_module.list_accounts.fn(request)

			assert isinstance(result, list)
			assert len(result) == 1
			assert isinstance(result[0], Account)
			assert result[0].id == '123'
			assert result[0].name == 'Test Account'

			mock_client.list_accounts.assert_called_once_with(type=AccountTypeFilter.asset)

	@pytest.mark.asyncio
	async def test_get_account(self, sample_account: Account):
		"""Test get_account tool"""
		with patch('lampyrid.server._client') as mock_client:
			mock_client.get_account = AsyncMock(return_value=sample_account)

			request = GetAccountRequest(id='123')
			result = await server_module.get_account.fn(request)

			assert isinstance(result, Account)
			assert result.id == '123'
			assert result.name == 'Test Account'
			mock_client.get_account.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_search_accounts(self, sample_account_array: AccountArray):
		"""Test search_accounts tool"""
		with patch('lampyrid.server._client') as mock_client:
			mock_client.search_accounts = AsyncMock(return_value=sample_account_array)

			request = SearchAccountRequest(query='checking', type=AccountTypeFilter.asset)
			result = await server_module.search_accounts.fn(request)

			assert isinstance(result, list)
			assert len(result) == 1
			assert isinstance(result[0], Account)

			mock_client.search_accounts.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_create_withdrawal(self):
		"""Test create_withdrawal tool"""
		mock_transaction = Transaction(
			amount=100.0,
			description='Test withdrawal',
			type=TransactionType.withdrawal,
			source_id='1',
			destination_id='2',
		)

		with patch('lampyrid.server._client') as mock_client:
			mock_client.create_withdrawal = AsyncMock(return_value=mock_transaction)

			request = CreateWithdrawalRequest(
				amount=100.0, description='Test withdrawal', source_id='1', destination_name='Cash'
			)

			result = await server_module.create_withdrawal.fn(request)

			assert result == mock_transaction
			mock_client.create_withdrawal.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_create_deposit(self):
		"""Test create_deposit tool"""
		mock_transaction = Transaction(
			amount=200.0,
			description='Test deposit',
			type=TransactionType.deposit,
			source_id='1',
			destination_id='2',
		)

		with patch('lampyrid.server._client') as mock_client:
			mock_client.create_deposit = AsyncMock(return_value=mock_transaction)

			request = CreateDepositRequest(
				amount=200.0, description='Test deposit', source_name='Employer', destination_id='1'
			)

			result = await server_module.create_deposit.fn(request)

			assert result == mock_transaction
			mock_client.create_deposit.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_create_transfer(self):
		"""Test create_transfer tool"""
		mock_transaction = Transaction(
			amount=150.0,
			description='Test transfer',
			type=TransactionType.transfer,
			source_id='1',
			destination_id='2',
		)

		with patch('lampyrid.server._client') as mock_client:
			mock_client.create_transfer = AsyncMock(return_value=mock_transaction)

			request = CreateTransferRequest(
				amount=150.0, description='Test transfer', source_id='1', destination_id='2'
			)

			result = await server_module.create_transfer.fn(request)

			assert result == mock_transaction
			mock_client.create_transfer.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_list_accounts_empty_result(self):
		"""Test list_accounts with empty result"""
		empty_account_array = MagicMock()
		empty_account_array.data = []

		with patch('lampyrid.server._client') as mock_client:
			mock_client.list_accounts = AsyncMock(return_value=empty_account_array)

			request = ListAccountRequest(type=AccountTypeFilter.asset)
			result = await server_module.list_accounts.fn(request)

			assert isinstance(result, list)
			assert len(result) == 0

	@pytest.mark.asyncio
	async def test_search_accounts_empty_result(self):
		"""Test search_accounts with empty result"""
		empty_account_array = MagicMock()
		empty_account_array.data = []

		with patch('lampyrid.server._client') as mock_client:
			mock_client.search_accounts = AsyncMock(return_value=empty_account_array)

			request = SearchAccountRequest(query='nonexistent', type=AccountTypeFilter.asset)
			result = await server_module.search_accounts.fn(request)

			assert isinstance(result, list)
			assert len(result) == 0

	@pytest.mark.asyncio
	async def test_get_transactions(self, sample_transaction_array: TransactionArray):
		"""Test get_transactions tool"""
		with patch('lampyrid.server._client') as mock_client:
			mock_client.get_transactions = AsyncMock(return_value=sample_transaction_array)

			request = GetTransactionsRequest(page=1, limit=50)
			result = await server_module.get_transactions.fn(request)

			assert isinstance(result, TransactionListResponse)
			assert len(result.transactions) == 1
			assert result.current_page == 1
			assert result.per_page == 50

			mock_client.get_transactions.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_search_transactions(self, sample_transaction_array: TransactionArray):
		"""Test search_transactions tool"""
		with patch('lampyrid.server._client') as mock_client:
			mock_client.search_transactions = AsyncMock(return_value=sample_transaction_array)

			request = SearchTransactionsRequest(query='groceries', page=1, limit=50)
			result = await server_module.search_transactions.fn(request)

			assert isinstance(result, TransactionListResponse)
			assert len(result.transactions) == 1
			assert result.current_page == 1
			assert result.per_page == 50

			mock_client.search_transactions.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_get_transaction(self):
		"""Test get_transaction tool"""
		from datetime import datetime

		mock_transaction = Transaction(
			amount=50.0,
			description='Test transaction',
			type=TransactionType.withdrawal,
			date=datetime.now(),
			source_id='1',
			destination_id='2',
		)

		with patch('lampyrid.server._client') as mock_client:
			mock_client.get_transaction = AsyncMock(return_value=mock_transaction)

			request = GetTransactionRequest(id='123')
			result = await server_module.get_transaction.fn(request)

			assert isinstance(result, Transaction)
			assert result.amount == 50.0
			assert result.description == 'Test transaction'
			mock_client.get_transaction.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_delete_transaction(self):
		"""Test delete_transaction tool"""
		with patch('lampyrid.server._client') as mock_client:
			mock_client.delete_transaction = AsyncMock(return_value=True)

			request = DeleteTransactionRequest(id='123')
			result = await server_module.delete_transaction.fn(request)

			assert result is True
			mock_client.delete_transaction.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_client_error_propagation(self):
		"""Test that client errors are properly propagated"""
		with patch('lampyrid.server._client') as mock_client:
			mock_client.list_accounts = AsyncMock(side_effect=Exception('API Error'))

			request = ListAccountRequest(type=AccountTypeFilter.asset)

			with pytest.raises(Exception, match='API Error'):
				await server_module.list_accounts.fn(request)

	@pytest.mark.asyncio
	async def test_list_budgets(self, sample_budget_array):
		"""Test list_budgets tool"""
		with patch('lampyrid.server._client') as mock_client:
			mock_client.list_budgets = AsyncMock(return_value=sample_budget_array)

			request = ListBudgetsRequest(active=True)
			result = await server_module.list_budgets.fn(request)

			assert isinstance(result, list)
			assert len(result) == 1
			assert isinstance(result[0], Budget)
			assert result[0].id == '789'
			assert result[0].name == 'Groceries'
			assert result[0].active is True

			mock_client.list_budgets.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_create_bulk_transactions(self):
		"""Test create_bulk_transactions tool"""
		from datetime import datetime

		# Create sample transactions for bulk creation
		transactions = [
			Transaction(
				amount=50.0,
				description='Grocery shopping',
				type=TransactionType.withdrawal,
				date=datetime.now(),
				source_id='1',
				destination_name='Supermarket',
			),
			Transaction(
				amount=25.0,
				description='Coffee',
				type=TransactionType.withdrawal,
				date=datetime.now(),
				source_id='1',
				destination_name='Cafe',
			),
			Transaction(
				amount=100.0,
				description='Salary',
				type=TransactionType.deposit,
				date=datetime.now(),
				source_name='Employer',
				destination_id='1',
			),
		]

		with patch('lampyrid.server._client') as mock_client:
			mock_client.create_bulk_transactions = AsyncMock(return_value=transactions)

			request = CreateBulkTransactionsRequest(transactions=transactions)
			result = await server_module.create_bulk_transactions.fn(request)

			assert isinstance(result, list)
			assert len(result) == 3
			assert all(isinstance(trx, Transaction) for trx in result)

			# Verify transaction details
			assert result[0].description == 'Grocery shopping'
			assert result[0].amount == 50.0
			assert result[1].description == 'Coffee'
			assert result[1].amount == 25.0
			assert result[2].description == 'Salary'
			assert result[2].amount == 100.0

			mock_client.create_bulk_transactions.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_update_transaction(self):
		"""Test update_transaction tool"""
		from datetime import datetime

		# Create a mock updated transaction
		updated_transaction = Transaction(
			id='123',
			amount=75.0,
			description='Updated grocery shopping',
			type=TransactionType.withdrawal,
			date=datetime.now(),
			source_id='1',
			destination_id='2',
		)

		with patch('lampyrid.server._client') as mock_client:
			mock_client.update_transaction = AsyncMock(return_value=updated_transaction)

			request = UpdateTransactionRequest(
				transaction_id='123', amount=75.0, description='Updated grocery shopping'
			)
			result = await server_module.update_transaction.fn(request)

			assert isinstance(result, Transaction)
			assert result.id == '123'
			assert result.amount == 75.0
			assert result.description == 'Updated grocery shopping'

			mock_client.update_transaction.assert_called_once_with(request)

	@pytest.mark.asyncio
	async def test_bulk_update_transactions(self):
		"""Test bulk_update_transactions tool"""
		from datetime import datetime

		# Create mock updated transactions
		updated_transactions = [
			Transaction(
				id='123',
				amount=100.0,
				description='Updated transaction 1',
				type=TransactionType.withdrawal,
				date=datetime.now(),
				source_id='1',
				destination_id='2',
			),
			Transaction(
				id='124',
				amount=200.0,
				description='Updated transaction 2',
				type=TransactionType.deposit,
				date=datetime.now(),
				source_id='3',
				destination_id='1',
			),
		]

		with patch('lampyrid.server._client') as mock_client:
			mock_client.bulk_update_transactions = AsyncMock(return_value=updated_transactions)

			request = BulkUpdateTransactionsRequest(
				updates=[
					UpdateTransactionRequest(transaction_id='123', amount=100.0),
					UpdateTransactionRequest(
						transaction_id='124', description='Updated transaction 2'
					),
				]
			)
			result = await server_module.bulk_update_transactions.fn(request)

			assert isinstance(result, list)
			assert len(result) == 2
			assert all(isinstance(trx, Transaction) for trx in result)
			assert result[0].id == '123'
			assert result[0].amount == 100.0
			assert result[1].id == '124'
			assert result[1].description == 'Updated transaction 2'

			mock_client.bulk_update_transactions.assert_called_once_with(request)
