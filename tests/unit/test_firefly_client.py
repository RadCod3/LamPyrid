import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from lampyrid.clients.firefly import FireflyClient
from lampyrid.models.firefly_models import AccountArray, AccountTypeFilter
from lampyrid.models.lampyrid_models import (
	CreateWithdrawalRequest,
	CreateDepositRequest,
	CreateTransferRequest,
	DeleteTransactionRequest,
	GetAccountRequest,
	GetTransactionRequest,
	GetTransactionsRequest,
	ListBudgetsRequest,
	SearchAccountRequest,
	SearchTransactionsRequest,
	UpdateTransactionBudgetRequest,
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
	async def test_update_transaction_budget(self, sample_transaction_single):
		"""Test updating a transaction's budget allocation"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = sample_transaction_single.model_dump()
			mock_client.put.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = UpdateTransactionBudgetRequest(
					transaction_id='456',
					budget_id='789',
					budget_name='Groceries',
				)

				result = await client.update_transaction_budget(request)

				assert result.amount == 100.0
				mock_client.put.assert_called_once_with(
					'/api/v1/transactions/456',
					json={
						'apply_rules': False,
						'fire_webhooks': True,
						'group_title': None,
						'transactions': [{'budget_id': '789', 'budget_name': 'Groceries'}],
					},
				)
				mock_response.raise_for_status.assert_called_once()
