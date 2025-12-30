import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock

from lampyrid.clients.firefly import FireflyClient
from lampyrid.models.lampyrid_models import (
	SearchAccountRequest,
	CreateWithdrawalRequest,
	GetBudgetRequest,
	GetBudgetSpendingRequest,
	GetBudgetSummaryRequest,
	GetAvailableBudgetRequest,
)
from lampyrid.models.firefly_models import AccountTypeFilter


@pytest.mark.integration
class TestFireflyIntegration:
	"""Integration tests for Firefly III client

	These tests mock HTTP responses but test the full integration
	between the client and the Firefly III API format.
	"""

	@pytest.mark.asyncio
	async def test_full_account_listing_flow(self):
		"""Test complete account listing flow"""
		# Mock HTTP response matching Firefly III API format
		mock_response_data = {
			'data': [
				{
					'id': '1',
					'type': 'accounts',
					'attributes': {
						'name': 'Checking Account',
						'type': 'asset',
						'currency_code': 'USD',
						'current_balance': '1500.00',
					},
				},
				{
					'id': '2',
					'type': 'accounts',
					'attributes': {
						'name': 'Savings Account',
						'type': 'asset',
						'currency_code': 'USD',
						'current_balance': '5000.00',
					},
				},
			],
			'meta': {
				'pagination': {
					'total': 2,
					'count': 2,
					'per_page': 50,
					'current_page': 1,
					'total_pages': 1,
				}
			},
		}

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			# Mock the HTTP response
			mock_response = MagicMock()
			mock_response.json.return_value = mock_response_data
			mock_response.raise_for_status.return_value = None
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				# Test the full flow
				client = FireflyClient()
				result = await client.list_accounts(type=AccountTypeFilter.asset)

				# Verify the result structure
				assert len(result.data) == 2
				assert result.data[0].id == '1'
				assert result.data[0].attributes.name == 'Checking Account'
				assert result.data[0].attributes.current_balance == '1500.00'
				assert result.data[1].id == '2'
				assert result.data[1].attributes.name == 'Savings Account'

	@pytest.mark.asyncio
	async def test_transaction_creation_flow(self):
		"""Test complete transaction creation flow"""
		mock_response_data = {
			'data': {
				'id': '123',
				'type': 'transactions',
				'attributes': {
					'transactions': [
						{
							'amount': '100.00',
							'description': 'Test withdrawal',
							'type': 'withdrawal',
							'date': '2025-01-01T12:00:00Z',
							'source_id': '1',
							'destination_id': '2',
						}
					]
				},
				'links': {'self': 'https://demo.firefly-iii.org/api/v1/transactions/123'},
			}
		}

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = mock_response_data
			mock_response.raise_for_status.return_value = None
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

				# Verify the transaction was created correctly
				assert result.amount == 100.0
				assert result.description == 'Test withdrawal'

				# Verify the correct API call was made
				mock_client.post.assert_called_once()
				assert mock_client.post.call_args[0][0] == '/api/v1/transactions'

	@pytest.mark.asyncio
	async def test_search_accounts_flow(self):
		"""Test complete account search flow"""
		mock_response_data = {
			'data': [
				{
					'id': '3',
					'type': 'accounts',
					'attributes': {
						'name': 'Business Checking',
						'type': 'asset',
						'currency_code': 'USD',
						'current_balance': '2500.00',
					},
				}
			],
			'meta': {'pagination': {'total': 1}},
		}

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			mock_response = MagicMock()
			mock_response.json.return_value = mock_response_data
			mock_response.raise_for_status.return_value = None
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()
				request = SearchAccountRequest(query='business', type=AccountTypeFilter.asset)

				result = await client.search_accounts(request)

				# Verify search worked correctly
				assert len(result.data) == 1
				assert result.data[0].attributes.name == 'Business Checking'

				# Verify correct search parameters
				mock_client.get.assert_called_once_with(
					'/api/v1/search/accounts',
					params={
						'query': 'business',
						'type': 'asset',
						'field': 'name',
						'limit': 50,
						'page': 1,
					},
				)

	@pytest.mark.asyncio
	async def test_error_handling_integration(self):
		"""Test error handling in integration scenario"""
		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			# Simulate HTTP error
			mock_response = MagicMock()
			mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
				'Unauthorized', request=MagicMock(), response=MagicMock()
			)
			mock_client.get.return_value = mock_response

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'invalid-token'

				client = FireflyClient()

				with pytest.raises(httpx.HTTPStatusError):
					await client.list_accounts()

	@pytest.mark.asyncio
	async def test_budget_operations_flow(self):
		"""Test complete budget operations flow"""
		from datetime import date

		# Mock response for getting a budget
		budget_response_data = {
			'data': {
				'id': '789',
				'type': 'budgets',
				'attributes': {
					'name': 'Groceries',
					'active': True,
					'notes': 'Monthly grocery budget',
					'order': 1,
				},
			}
		}

		# Mock response for budget limits (spending data)
		limits_response_data = {
			'data': [
				{
					'id': '111',
					'type': 'budget_limits',
					'attributes': {
						'start': '2023-01-01T00:00:00+00:00',
						'end': '2023-01-31T23:59:59+00:00',
						'budget_id': '789',
						'amount': '500.00',
						'spent': '-123.45',
						'notes': 'Monthly limit for groceries',
					},
				}
			],
			'meta': {'pagination': {'total': 1}},
		}

		# Mock response for budget array (for summary)
		budgets_array_response = {
			'data': [
				{
					'id': '789',
					'type': 'budgets',
					'attributes': {
						'name': 'Groceries',
						'active': True,
						'notes': 'Monthly grocery budget',
						'order': 1,
					},
				}
			],
			'meta': {'pagination': {'total': 1}},
		}

		# Mock response for available budget
		available_budget_response = {
			'data': [
				{
					'id': '222',
					'type': 'available_budgets',
					'attributes': {
						'currency_code': 'USD',
						'amount': '1000.00',
						'start': '2023-01-01T00:00:00+00:00',
						'end': '2023-01-31T23:59:59+00:00',
						'spent_in_budgets': [
							{
								'sum': '200.00',
								'currency_code': 'USD',
								'currency_symbol': '$',
								'currency_decimal_places': 2,
							}
						],
						'spent_outside_budget': [
							{
								'sum': '50.00',
								'currency_code': 'USD',
								'currency_symbol': '$',
								'currency_decimal_places': 2,
							}
						],
					},
				}
			],
			'meta': {'pagination': {'total': 1}},
		}

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()

				# Test 1: Get budget
				mock_response = MagicMock()
				mock_response.json.return_value = budget_response_data
				mock_response.raise_for_status.return_value = None
				mock_client.get.return_value = mock_response

				request = GetBudgetRequest(id='789')
				result = await client.get_budget(request)

				assert result.id == '789'
				assert result.name == 'Groceries'
				mock_client.get.assert_called_with('/api/v1/budgets/789')

				# Reset mock for next test
				mock_client.reset_mock()

				# Test 2: Get budget spending
				budget_mock = MagicMock()
				budget_mock.json.return_value = budget_response_data
				budget_mock.raise_for_status.return_value = None

				limits_mock = MagicMock()
				limits_mock.json.return_value = limits_response_data
				limits_mock.raise_for_status.return_value = None

				mock_client.get.side_effect = [budget_mock, limits_mock]

				spending_request = GetBudgetSpendingRequest(
					budget_id='789',
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)
				spending_result = await client.get_budget_spending(spending_request)

				assert spending_result.budget_id == '789'
				assert spending_result.budget_name == 'Groceries'
				assert spending_result.spent == 123.45  # abs(spent)
				assert spending_result.budgeted == 500.0
				assert spending_result.remaining == 376.55

				# Reset mock for next test
				mock_client.reset_mock()

				# Test 3: Get budget summary
				budgets_mock = MagicMock()
				budgets_mock.json.return_value = budgets_array_response
				budgets_mock.raise_for_status.return_value = None

				budget_detail_mock = MagicMock()
				budget_detail_mock.json.return_value = budget_response_data
				budget_detail_mock.raise_for_status.return_value = None

				limits_detail_mock = MagicMock()
				limits_detail_mock.json.return_value = limits_response_data
				limits_detail_mock.raise_for_status.return_value = None

				mock_client.get.side_effect = [budgets_mock, budget_detail_mock, limits_detail_mock]

				summary_request = GetBudgetSummaryRequest(
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)
				summary_result = await client.get_budget_summary(summary_request)

				assert len(summary_result.budgets) == 1
				assert summary_result.total_spent == 123.45
				assert summary_result.total_budgeted == 500.0

				# Reset mock for final test
				mock_client.reset_mock()

				# Test 4: Get available budget
				available_mock = MagicMock()
				available_mock.json.return_value = available_budget_response
				available_mock.raise_for_status.return_value = None
				mock_client.get.return_value = available_mock
				mock_client.get.side_effect = None  # Clear side_effect

				available_request = GetAvailableBudgetRequest(
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)
				available_result = await client.get_available_budget(available_request)

				assert available_result.amount == 1000.0
				assert available_result.currency_code == 'USD'
				assert available_result.start_date == date(2023, 1, 1)
				assert available_result.end_date == date(2023, 1, 31)

				mock_client.get.assert_called_with(
					'/api/v1/available-budgets', params={'start': '2023-01-01', 'end': '2023-01-31'}
				)

	@pytest.mark.asyncio
	async def test_budget_error_scenarios(self):
		"""Test budget-related error handling scenarios"""
		from datetime import date

		with patch('lampyrid.clients.firefly.httpx.AsyncClient') as mock_client_class:
			mock_client = AsyncMock()
			mock_client_class.return_value = mock_client

			with patch('lampyrid.clients.firefly.settings') as mock_settings:
				mock_settings.firefly_base_url = 'https://firefly.example.com'
				mock_settings.firefly_token = 'test-token'

				client = FireflyClient()

				# Test error handling for non-existent budget
				mock_response = MagicMock()
				mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
					'Not Found', request=MagicMock(), response=MagicMock()
				)
				mock_client.get.return_value = mock_response

				request = GetBudgetRequest(id='999')

				with pytest.raises(httpx.HTTPStatusError):
					await client.get_budget(request)

				# Test error handling for budget spending
				request = GetBudgetSpendingRequest(
					budget_id='999',
					start_date=date(2023, 1, 1),
					end_date=date(2023, 1, 31),
				)

				with pytest.raises(httpx.HTTPStatusError):
					await client.get_budget_spending(request)
