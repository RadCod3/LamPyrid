"""Unit tests for TransactionService."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from lampyrid.models.lampyrid_models import SearchTransactionsRequest
from lampyrid.services.transactions import TransactionService


class TestTransactionServiceSearchSanitization:
    """Test cases for search_transactions input sanitization."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock FireflyClient."""
        client = MagicMock()
        client.search_transactions = AsyncMock()
        # Return a mock TransactionArray with required structure
        mock_response = MagicMock()
        mock_response.data = []
        mock_response.meta = MagicMock()
        mock_response.meta.pagination = MagicMock()
        mock_response.meta.pagination.total = 0
        mock_response.meta.pagination.count = 0
        mock_response.meta.pagination.per_page = 50
        mock_response.meta.pagination.current_page = 1
        mock_response.meta.pagination.total_pages = 0
        client.search_transactions.return_value = mock_response
        return client

    @pytest.fixture
    def service(self, mock_client):
        """Create a TransactionService with mock client."""
        return TransactionService(mock_client)

    def _get_query_from_call(self, mock_client) -> str:
        """Extract the query string passed to search_transactions."""
        call_args = mock_client.search_transactions.call_args
        return call_args.kwargs.get('query', call_args.args[0] if call_args.args else '')

    @pytest.mark.asyncio
    async def test_search_transactions_sanitizes_description_contains(self, service, mock_client):
        """Test that description_contains values are properly sanitized."""
        req = SearchTransactionsRequest(description_contains='test "quoted" value')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Should escape quotes and wrap in quotes since it contains special chars
        assert 'description_contains:"test \\"quoted\\" value"' in query

    @pytest.mark.asyncio
    async def test_search_transactions_sanitizes_category(self, service, mock_client):
        """Test that category values are properly sanitized."""
        req = SearchTransactionsRequest(category='Food & "Dining"')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Should escape quotes and wrap in quotes since it contains special chars
        assert 'category_is:"Food & \\"Dining\\""' in query

    @pytest.mark.asyncio
    async def test_search_transactions_sanitizes_budget(self, service, mock_client):
        """Test that budget values are properly sanitized."""
        req = SearchTransactionsRequest(budget='Monthly "Expenses"')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Should escape quotes and wrap in quotes since it contains special chars
        assert 'budget_is:"Monthly \\"Expenses\\""' in query

    @pytest.mark.asyncio
    async def test_search_transactions_sanitizes_account_contains(self, service, mock_client):
        """Test that account_contains values are properly sanitized."""
        req = SearchTransactionsRequest(account_contains='Bank "Account"')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Should escape quotes and wrap in quotes since it contains special chars
        assert 'account_contains:"Bank \\"Account\\""' in query

    @pytest.mark.asyncio
    async def test_search_transactions_handles_backslashes_in_values(self, service, mock_client):
        """Test that backslashes in values are properly escaped."""
        req = SearchTransactionsRequest(description_contains='path\\to\\file')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Backslashes should be escaped (doubled)
        assert 'description_contains:path\\\\to\\\\file' in query

    @pytest.mark.asyncio
    async def test_search_transactions_handles_spaces_in_values(self, service, mock_client):
        """Test that values with spaces are properly quoted."""
        req = SearchTransactionsRequest(category='Food and Drinks')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Should be wrapped in quotes due to spaces
        assert 'category_is:"Food and Drinks"' in query

    @pytest.mark.asyncio
    async def test_search_transactions_simple_values_not_quoted(self, service, mock_client):
        """Test that simple values without special chars are not unnecessarily quoted."""
        req = SearchTransactionsRequest(category='Groceries')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Should NOT be wrapped in quotes (no special chars)
        assert 'category_is:Groceries' in query
        assert 'category_is:"Groceries"' not in query

    @pytest.mark.asyncio
    async def test_search_transactions_handles_mixed_special_chars(self, service, mock_client):
        """Test values with both quotes and backslashes."""
        req = SearchTransactionsRequest(description_contains='test "quoted" and\\backslash')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Both quotes and backslashes should be escaped, wrapped in quotes
        assert 'description_contains:"test \\"quoted\\" and\\\\backslash"' in query

    @pytest.mark.asyncio
    async def test_search_transactions_handles_single_quotes(self, service, mock_client):
        """Test that single quotes trigger quoting (per _sanitize_value logic)."""
        req = SearchTransactionsRequest(budget="don't spend")

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # Should be wrapped in quotes due to single quote
        assert 'budget_is:"don\'t spend"' in query

    @pytest.mark.asyncio
    async def test_search_transactions_multiple_sanitized_fields(self, service, mock_client):
        """Test that multiple fields are all properly sanitized."""
        req = SearchTransactionsRequest(
            description_contains='desc "test"',
            category='cat "test"',
            budget='budget "test"',
            account_contains='account "test"',
        )

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # All fields should be properly sanitized
        assert 'description_contains:"desc \\"test\\""' in query
        assert 'category_is:"cat \\"test\\""' in query
        assert 'budget_is:"budget \\"test\\""' in query
        assert 'account_contains:"account \\"test\\""' in query

    @pytest.mark.asyncio
    async def test_search_transactions_non_string_fields_unchanged(self, service, mock_client):
        """Test that non-string fields like account_id are not affected."""
        req = SearchTransactionsRequest(account_id='123')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        # account_id should be formatted as-is (string ID)
        assert 'account_id:123' in query


class TestTransactionServiceSearchQueryConstruction:
    """Test cases for search_transactions query construction."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock FireflyClient."""
        client = MagicMock()
        client.search_transactions = AsyncMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_response.meta = MagicMock()
        mock_response.meta.pagination = MagicMock()
        mock_response.meta.pagination.total = 0
        mock_response.meta.pagination.count = 0
        mock_response.meta.pagination.per_page = 50
        mock_response.meta.pagination.current_page = 1
        mock_response.meta.pagination.total_pages = 0
        client.search_transactions.return_value = mock_response
        return client

    @pytest.fixture
    def service(self, mock_client):
        """Create a TransactionService with mock client."""
        return TransactionService(mock_client)

    def _get_query_from_call(self, mock_client) -> str:
        """Extract the query string passed to search_transactions."""
        call_args = mock_client.search_transactions.call_args
        return call_args.kwargs.get('query', call_args.args[0] if call_args.args else '')

    @pytest.mark.asyncio
    async def test_search_transactions_with_raw_query(self, service, mock_client):
        """Test that raw query is included in the final query."""
        req = SearchTransactionsRequest(query='some raw query')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        assert 'some raw query' in query

    @pytest.mark.asyncio
    async def test_search_transactions_with_type_filter(self, service, mock_client):
        """Test that type filter is properly formatted."""
        req = SearchTransactionsRequest(type='withdrawal')

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        assert 'type:withdrawal' in query

    @pytest.mark.asyncio
    async def test_search_transactions_with_amount_filters(self, service, mock_client):
        """Test that amount filters are properly formatted."""
        req = SearchTransactionsRequest(amount_equals=100.50, amount_more=50.0, amount_less=200.0)

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        assert 'amount:100.5' in query
        assert 'more:50.0' in query
        assert 'less:200.0' in query

    @pytest.mark.asyncio
    async def test_search_transactions_with_date_filters(self, service, mock_client):
        """Test that date filters are properly formatted."""
        req = SearchTransactionsRequest(
            date_on=date(2024, 1, 15),
            date_after=date(2024, 1, 1),
            date_before=date(2024, 1, 31),
        )

        await service.search_transactions(req)

        query = self._get_query_from_call(mock_client)
        assert 'date_on:2024-01-15' in query
        assert 'date_after:2024-01-01' in query
        assert 'date_before:2024-01-31' in query

    @pytest.mark.asyncio
    async def test_search_transactions_passes_pagination_params(self, service, mock_client):
        """Test that pagination parameters are passed to client."""
        req = SearchTransactionsRequest(query='test', page=2, limit=25)

        await service.search_transactions(req)

        mock_client.search_transactions.assert_called_once()
        call_kwargs = mock_client.search_transactions.call_args.kwargs
        assert call_kwargs['page'] == 2
        assert call_kwargs['limit'] == 25
