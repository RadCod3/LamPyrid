import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import lampyrid.server as server_module
from lampyrid.models.lampyrid_models import (
	Account,
	Budget,
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
	UpdateTransactionBudgetRequest,
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
	async def test_update_transaction_budget(self):
		"""Test update_transaction_budget tool"""
		from datetime import datetime

		mock_transaction = Transaction(
			amount=50.0,
			description='Test transaction',
			type=TransactionType.withdrawal,
			date=datetime.now(),
			source_id='1',
			destination_id='2',
			budget_id='789',
			budget_name='Groceries',
		)

		with patch('lampyrid.server._client') as mock_client:
			mock_client.update_transaction_budget = AsyncMock(return_value=mock_transaction)

			request = UpdateTransactionBudgetRequest(
				transaction_id='456',
				budget_id='789',
				budget_name='Groceries',
			)
			result = await server_module.update_transaction_budget.fn(request)

			assert isinstance(result, Transaction)
			assert result.budget_id == '789'
			assert result.budget_name == 'Groceries'
			mock_client.update_transaction_budget.assert_called_once_with(request)
