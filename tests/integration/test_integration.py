import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock

from lampyrid.clients.firefly import FireflyClient
from lampyrid.models.lampyrid_models import SearchAccountRequest, CreateWithdrawalRequest
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
