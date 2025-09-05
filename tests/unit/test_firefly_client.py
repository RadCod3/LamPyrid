import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from lampyrid.clients.firefly import FireflyClient
from lampyrid.models.firefly_models import AccountArray, AccountTypeFilter
from lampyrid.models.lampyrid_models import (
	CreateBulkTransactionsRequest,
	CreateWithdrawalRequest,
	CreateDepositRequest,
	CreateTransferRequest,
	DeleteTransactionRequest,
	GetAccountRequest,
	GetAvailableBudgetRequest,
	GetBudgetRequest,
	GetBudgetSpendingRequest,
	GetBudgetSummaryRequest,
	GetTransactionRequest,
	GetTransactionsRequest,
	ListBudgetsRequest,
	SearchAccountRequest,
	SearchTransactionsRequest,
	Transaction,
	TransactionType,
	UpdateTransactionRequest,
)


class TestFireflyClient:
	"""Test FireflyClient"""

	@patch('lampyrid.clients.firefly.settings')
	def test_client_initialization(self, mock_settings):
		"""Test FireflyClient initialization"""
		mock_settings.firefly_base_url = 'https://firefly.example.com/'
		mock_settings.firefly_token = 'test-token'

		with patch('httpx.AsyncClient') as mock_client:
			FireflyClient()

			mock_client.assert_called_once_with(
				base_url='https://firefly.example.com',
				headers={
					'Authorization': 'Bearer test-token',
					'Accept': 'application/json',
					'Content-Type': 'application/json',
				},
				timeout=30.0,
			)

	@pytest.mark.asyncio
	async def test_list_accounts(self, sample_account_array):
		"""Test listing accounts"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_account_array.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				result = await client.list_accounts(page=1, type=AccountTypeFilter.asset)

				assert isinstance(result, AccountArray)
				mock_client.get.assert_called_once_with(
					'/api/v1/accounts', params={'page': 1, 'type': 'asset'}
				)
				mock_response.raise_for_status.assert_called_once()

	@pytest.mark.asyncio
	async def test_search_accounts(self):
		"""Test searching accounts"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = {'data': [], 'meta': {'pagination': {'total': 0}}}
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = SearchAccountRequest(query='checking', type=AccountTypeFilter.asset)

				await client.search_accounts(request)

				mock_client.get.assert_called_once_with(
					'/api/v1/search/accounts',
					params={
						'query': 'checking',
						'type': 'asset',
						'field': 'name',
						'limit': 50,
						'page': 1,
					},
				)

	@pytest.mark.asyncio
	async def test_get_account(self, sample_account_single):
		"""Test getting a single account"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_account_single.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetAccountRequest(id='123')

				result = await client.get_account(request)

				assert result.id == '123'
				assert result.name == 'Test Account'
				assert result.currency_code == 'USD'
				assert result.current_balance == 1000.0
				mock_client.get.assert_called_once_with('/api/v1/accounts/123')
				mock_response.raise_for_status.assert_called_once()

	@pytest.mark.asyncio
	async def test_create_withdrawal(self, sample_transaction_single):
		"""Test creating a withdrawal"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_single.model_dump()
			mock_client.post.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = CreateWithdrawalRequest(
					amount=100.0,
					description='Test withdrawal',
					source_id='1',
					destination_name='Cash',
				)

				result = await client.create_withdrawal(request)

				assert result.amount == 100.0
				assert result.description == 'Test transaction'
				# Verify the endpoint was called correctly
				mock_client.post.assert_called_once()
				assert mock_client.post.call_args[0][0] == '/api/v1/transactions'

	@pytest.mark.asyncio
	async def test_create_deposit(self, sample_transaction_single):
		"""Test creating a deposit"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_single.model_dump()
			mock_client.post.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = CreateDepositRequest(
					amount=200.0,
					description='Test deposit',
					source_name='Employer',
					destination_id='1',
				)

				result = await client.create_deposit(request)

				assert result.amount == 100.0
				# Verify the endpoint was called correctly
				mock_client.post.assert_called_once()
				assert mock_client.post.call_args[0][0] == '/api/v1/transactions'

	@pytest.mark.asyncio
	async def test_create_transfer(self, sample_transaction_single):
		"""Test creating a transfer"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_single.model_dump()
			mock_client.post.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = CreateTransferRequest(
					amount=150.0, description='Test transfer', source_id='1', destination_id='2'
				)

				result = await client.create_transfer(request)

				assert result.amount == 100.0
				# Verify the endpoint was called correctly
				mock_client.post.assert_called_once()
				assert mock_client.post.call_args[0][0] == '/api/v1/transactions'

	@pytest.mark.asyncio
	async def test_http_error_handling(self):
		"""Test HTTP error handling"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
				'Bad Request', request=MagicMock(), response=MagicMock()
			)
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()

				with pytest.raises(httpx.HTTPStatusError):
					await client.list_accounts()

	@pytest.mark.asyncio
	async def test_get_transactions(self, sample_transaction_array):
		"""Test getting transactions"""
		from datetime import date
		from lampyrid.models.firefly_models import TransactionTypeFilter

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_array.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetTransactionsRequest(
					start_date=date(2023, 1, 1),
					end_date=date(2023, 12, 31),
					transaction_type=TransactionTypeFilter.withdrawal,
					page=1,
					limit=50,
				)

				result = await client.get_transactions(request)

				assert len(result.data) == 1
				assert result.data[0].id == '456'

				mock_client.get.assert_called_once_with(
					'/api/v1/transactions',
					params={
						'page': 1,
						'limit': 50,
						'start': '2023-01-01',
						'end': '2023-12-31',
						'type': 'withdrawal',
					},
				)

	@pytest.mark.asyncio
	async def test_search_transactions(self, sample_transaction_array):
		"""Test searching transactions"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_array.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = SearchTransactionsRequest(
					query='groceries',
					page=1,
					limit=25,
				)

				result = await client.search_transactions(request)

				assert len(result.data) == 1
				assert result.data[0].id == '456'

				mock_client.get.assert_called_once_with(
					'/api/v1/search/transactions',
					params={
						'query': 'groceries',
						'page': 1,
						'limit': 25,
					},
				)

	@pytest.mark.asyncio
	async def test_get_transaction(self, sample_transaction_single):
		"""Test getting a single transaction"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_single.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetTransactionRequest(id='123')

				result = await client.get_transaction(request)

				assert result.amount == 100.0
				assert result.description == 'Test transaction'
				mock_client.get.assert_called_once_with('/api/v1/transactions/123')
				mock_response.raise_for_status.assert_called_once()

	@pytest.mark.asyncio
	async def test_delete_transaction(self):
		"""Test deleting a transaction"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.status_code = 204
			mock_client.delete.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = DeleteTransactionRequest(id='123')

				result = await client.delete_transaction(request)

				assert result is True
				mock_client.delete.assert_called_once_with('/api/v1/transactions/123')
				mock_response.raise_for_status.assert_called_once()

	@pytest.mark.asyncio
	async def test_list_budgets(self, sample_budget_array):
		"""Test listing budgets"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_budget_array.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = ListBudgetsRequest(active=True)

				result = await client.list_budgets(request)

				assert len(result.data) == 1
				assert result.data[0].id == '789'
				mock_client.get.assert_called_once_with('/api/v1/budgets', params={'active': True})
				mock_response.raise_for_status.assert_called_once()

	@pytest.mark.asyncio
	async def test_list_budgets_no_filter(self, sample_budget_array):
		"""Test listing budgets without filter"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_budget_array.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = ListBudgetsRequest()

				result = await client.list_budgets(request)

				assert len(result.data) == 1
				mock_client.get.assert_called_once_with('/api/v1/budgets', params={})

	@pytest.mark.asyncio
	async def test_create_withdrawal_with_budget(self, sample_transaction_single):
		"""Test creating a withdrawal with budget allocation"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_single.model_dump()
			mock_client.post.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = CreateWithdrawalRequest(
					amount=100.0,
					description='Test withdrawal',
					source_id='1',
					destination_name='Cash',
					budget_id='789',
					budget_name='Groceries',
				)

				result = await client.create_withdrawal(request)

				assert result.amount == 100.0
				# Verify the endpoint was called correctly
				mock_client.post.assert_called_once()
				assert mock_client.post.call_args[0][0] == '/api/v1/transactions'

				# Check that budget information was included in the payload
				call_args = mock_client.post.call_args
				payload = call_args[1]['json']
				assert payload['transactions'][0]['budget_id'] == '789'
				assert payload['transactions'][0]['budget_name'] == 'Groceries'

	@pytest.mark.asyncio
	async def test_get_budget(self, sample_budget_single):
		"""Test getting a single budget"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_budget_single.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetBudgetRequest(id='789')

				result = await client.get_budget(request)

				assert result.id == '789'
				assert result.name == 'Groceries'
				assert result.active is True
				mock_client.get.assert_called_once_with('/api/v1/budgets/789')
				mock_response.raise_for_status.assert_called_once()

	@pytest.mark.asyncio
	async def test_get_budget_spending(self, sample_budget_single, sample_budget_limit_array):
		"""Test getting budget spending data"""
		from datetime import date

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			# Mock responses for budget info and spending data
			budget_response = MagicMock()
			budget_response.json.return_value = sample_budget_single.model_dump()

			limits_response = MagicMock()
			limits_response.json.return_value = sample_budget_limit_array.model_dump()

			# Set up the call sequence
			mock_client.get.side_effect = [budget_response, limits_response]

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetBudgetSpendingRequest(
					budget_id='789',
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)

				result = await client.get_budget_spending(request)

				assert result.budget_id == '789'
				assert result.budget_name == 'Groceries'
				assert result.spent == 123.45  # abs(spent) from fixture
				assert result.budgeted == 500.0
				assert result.remaining == 376.55
				assert (
					abs(result.percentage_spent - 24.69) < 0.01
				)  # Account for floating point precision

				# Verify API calls
				assert mock_client.get.call_count == 2
				mock_client.get.assert_any_call('/api/v1/budgets/789')
				mock_client.get.assert_any_call(
					'/api/v1/budgets/789/limits',
					params={'start': '2023-01-01', 'end': '2023-01-31'},
				)

	@pytest.mark.asyncio
	async def test_get_budget_summary(
		self, sample_budget_array, sample_budget_single, sample_budget_limit_array
	):
		"""Test getting budget summary"""
		from datetime import date

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			# Mock responses
			budgets_response = MagicMock()
			budgets_response.json.return_value = sample_budget_array.model_dump()

			budget_response = MagicMock()
			budget_response.json.return_value = sample_budget_single.model_dump()

			limits_response = MagicMock()
			limits_response.json.return_value = sample_budget_limit_array.model_dump()

			# Set up the call sequence: budgets list, then for each budget: budget info + limits
			mock_client.get.side_effect = [budgets_response, budget_response, limits_response]

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetBudgetSummaryRequest(
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)

				result = await client.get_budget_summary(request)

				assert len(result.budgets) == 1
				assert result.budgets[0].budget_id == '789'
				assert result.budgets[0].budget_name == 'Groceries'
				assert result.total_spent == 123.45
				assert result.total_budgeted == 500.0
				assert result.total_remaining == 376.55

				# Verify API calls
				assert mock_client.get.call_count == 3

	@pytest.mark.asyncio
	async def test_get_available_budget(self, sample_available_budget_array):
		"""Test getting available budget"""
		from datetime import date

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_available_budget_array.model_dump()
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetAvailableBudgetRequest(
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)

				result = await client.get_available_budget(request)

				assert result.amount == 1000.0
				assert result.currency_code == 'USD'
				assert result.start_date == date(2023, 1, 1)
				assert result.end_date == date(2023, 1, 31)

				mock_client.get.assert_called_once_with(
					'/api/v1/available-budgets', params={'start': '2023-01-01', 'end': '2023-01-31'}
				)
				mock_response.raise_for_status.assert_called_once()

	@pytest.mark.asyncio
	async def test_get_available_budget_empty_response(self):
		"""Test getting available budget with empty response"""
		from datetime import date

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			# Empty response
			mock_response = MagicMock()
			mock_response.json.return_value = {'data': [], 'meta': {'pagination': {'total': 0}}}
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetAvailableBudgetRequest(
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)

				result = await client.get_available_budget(request)

				# Should return default values
				assert result.amount == 0.0
				assert result.currency_code == 'USD'
				assert result.start_date == date(2023, 1, 1)
				assert result.end_date == date(2023, 1, 31)

	@pytest.mark.asyncio
	async def test_get_budget_spending_no_limits(self, sample_budget_single):
		"""Test getting budget spending data with no limits"""
		from datetime import date

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			# Mock responses
			budget_response = MagicMock()
			budget_response.json.return_value = sample_budget_single.model_dump()

			# Empty limits response
			limits_response = MagicMock()
			limits_response.json.return_value = {'data': [], 'meta': {'pagination': {'total': 0}}}

			mock_client.get.side_effect = [budget_response, limits_response]

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = GetBudgetSpendingRequest(
					budget_id='789',
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)

				result = await client.get_budget_spending(request)

				assert result.budget_id == '789'
				assert result.budget_name == 'Groceries'
				assert result.spent == 0.0
				assert result.budgeted is None
				assert result.remaining is None
				assert result.percentage_spent is None

	@pytest.mark.asyncio
	async def test_create_bulk_transactions(self, sample_transaction_single):
		"""Test creating multiple transactions in bulk"""
		from datetime import datetime

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			# Mock response for each transaction creation
			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_single.model_dump()
			mock_client.post.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

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
				]

				client = FireflyClient()
				request = CreateBulkTransactionsRequest(transactions=transactions)
				result = await client.create_bulk_transactions(request)

				# Should return list of created transactions
				assert isinstance(result, list)
				assert len(result) == 2

				# Verify each transaction was created via individual API calls
				assert mock_client.post.call_count == 2

				# Verify the correct API endpoint was called
				all_calls = mock_client.post.call_args_list
				assert all(call[0][0] == '/api/v1/transactions' for call in all_calls)

				# Verify payload structure
				first_call_json = all_calls[0][1]['json']
				assert first_call_json['apply_rules'] is False
				assert first_call_json['fire_webhooks'] is True
				assert first_call_json['error_if_duplicate_hash'] is False
				assert len(first_call_json['transactions']) == 1

				# Check first transaction details
				first_trx = first_call_json['transactions'][0]
				assert first_trx['type'] == 'withdrawal'
				assert first_trx['amount'] == '50.0'
				assert first_trx['description'] == 'Grocery shopping'
				assert first_trx['source_id'] == '1'
				assert first_trx['destination_name'] == 'Supermarket'

				mock_response.raise_for_status.assert_called()

	@pytest.mark.asyncio
	async def test_update_transaction(self, sample_transaction_single):
		"""Test updating an existing transaction"""

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			# Mock response for transaction update
			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_single.model_dump()
			mock_client.put.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = UpdateTransactionRequest(
					transaction_id='123',
					amount=75.0,
					description='Updated description',
					source_id='2',
					budget_id='456',
				)
				result = await client.update_transaction(request)

				# Should return updated transaction
				assert isinstance(result, Transaction)
				assert result.amount == 100.0  # From sample_transaction_single
				assert result.description == 'Test transaction'  # From sample_transaction_single

				# Verify the correct API call was made
				call_json = mock_client.put.call_args[1]['json']
				assert call_json['apply_rules'] is False
				assert call_json['fire_webhooks'] is True
				assert call_json['group_title'] is None
				assert len(call_json['transactions']) == 1

				# Verify the transaction fields that were set
				transaction_data = call_json['transactions'][0]
				assert transaction_data['amount'] == '75.0'
				assert transaction_data['description'] == 'Updated description'
				assert transaction_data['source_id'] == '2'
				assert transaction_data['budget_id'] == '456'

				# Verify endpoint was called correctly
				assert mock_client.put.call_args[0][0] == '/api/v1/transactions/123'
				mock_response.raise_for_status.assert_called_once()
