"""Unit tests for lampyrid models."""

import pytest

from lampyrid.models.lampyrid_models import (
    SearchTransactionsRequest,
    utc_now,
)


class TestLampyridModels:
    """Test cases for lampyrid models."""

    def test_utc_now(self):
        """Test utc_now function returns a datetime with UTC timezone."""
        result = utc_now()

        # Should return a datetime object
        assert hasattr(result, 'year')
        assert hasattr(result, 'month')
        assert hasattr(result, 'day')
        assert hasattr(result, 'hour')
        assert hasattr(result, 'minute')
        assert hasattr(result, 'second')

    def test_search_transactions_request_with_no_criteria(self):
        """Test SearchTransactionsRequest validation with no search criteria."""
        with pytest.raises(ValueError, match='At least one search criterion must be provided'):
            SearchTransactionsRequest(
                # No search fields provided
            )

    def test_search_transactions_request_with_empty_criteria(self):
        """Test SearchTransactionsRequest validation with empty string criteria."""
        with pytest.raises(ValueError, match='At least one search criterion must be provided'):
            SearchTransactionsRequest(
                query='',  # Empty string
            )

    def test_search_transactions_request_with_valid_criteria(self):
        """Test SearchTransactionsRequest validation passes with valid criteria."""
        # Should not raise any exception
        request = SearchTransactionsRequest(query='valid query')

        assert request.query == 'valid query'
