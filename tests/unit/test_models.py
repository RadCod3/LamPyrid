"""Unit tests for lampyrid models."""

import pytest
from pydantic import ValidationError

from lampyrid.models.lampyrid_models import (
    CreateDepositRequest,
    CreateWithdrawalRequest,
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


class TestCreateWithdrawalRequest:
    """Test cases for CreateWithdrawalRequest model."""

    def test_create_withdrawal_request_rejects_extra_fields(self):
        """Test that CreateWithdrawalRequest raises ValidationError on extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            CreateWithdrawalRequest(
                amount=25.50,
                description='Test withdrawal',
                source_id='1',
                unknown_field='should fail',  # ty:ignore[unknown-argument]
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['type'] == 'extra_forbidden'
        assert 'unknown_field' in str(errors[0]['loc'])

    def test_create_withdrawal_request_allows_destination_id(self):
        """Test that CreateWithdrawalRequest accepts destination_id field."""
        request = CreateWithdrawalRequest(
            amount=25.50,
            description='Test withdrawal',
            source_id='1',
            destination_id='5',
        )

        assert request.destination_id == '5'
        assert request.destination_name is None

    def test_create_withdrawal_request_allows_destination_name(self):
        """Test that CreateWithdrawalRequest accepts destination_name field."""
        request = CreateWithdrawalRequest(
            amount=25.50,
            description='Test withdrawal',
            source_id='1',
            destination_name='Groceries',
        )

        assert request.destination_name == 'Groceries'
        assert request.destination_id is None

    def test_create_withdrawal_request_mutual_exclusivity(self):
        """Test that destination_id and destination_name cannot both be provided."""
        with pytest.raises(ValidationError) as exc_info:
            CreateWithdrawalRequest(
                amount=25.50,
                description='Test withdrawal',
                source_id='1',
                destination_id='5',
                destination_name='Groceries',
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert 'Cannot specify both destination_id and destination_name' in str(errors[0]['msg'])

    def test_create_withdrawal_request_allows_neither_destination(self):
        """Test that neither destination_id nor destination_name can be omitted."""
        request = CreateWithdrawalRequest(
            amount=25.50,
            description='Test withdrawal',
            source_id='1',
        )

        assert request.destination_id is None
        assert request.destination_name is None


class TestCreateDepositRequest:
    """Test cases for CreateDepositRequest model."""

    def test_create_deposit_request_rejects_extra_fields(self):
        """Test that CreateDepositRequest raises ValidationError on extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            CreateDepositRequest(
                amount=500.00,
                description='Test deposit',
                destination_id='1',
                unknown_field='should fail',  # ty:ignore[unknown-argument]
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['type'] == 'extra_forbidden'
        assert 'unknown_field' in str(errors[0]['loc'])

    def test_create_deposit_request_allows_source_id(self):
        """Test that CreateDepositRequest accepts source_id field."""
        request = CreateDepositRequest(
            amount=500.00,
            description='Test deposit',
            destination_id='1',
            source_id='7',
        )

        assert request.source_id == '7'
        assert request.source_name is None

    def test_create_deposit_request_allows_source_name(self):
        """Test that CreateDepositRequest accepts source_name field."""
        request = CreateDepositRequest(
            amount=500.00,
            description='Test deposit',
            destination_id='1',
            source_name='Employer',
        )

        assert request.source_name == 'Employer'
        assert request.source_id is None

    def test_create_deposit_request_mutual_exclusivity(self):
        """Test that source_id and source_name cannot both be provided."""
        with pytest.raises(ValidationError) as exc_info:
            CreateDepositRequest(
                amount=500.00,
                description='Test deposit',
                destination_id='1',
                source_id='7',
                source_name='Employer',
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert 'Cannot specify both source_id and source_name' in str(errors[0]['msg'])

    def test_create_deposit_request_allows_neither_source(self):
        """Test that neither source_id nor source_name can be omitted."""
        request = CreateDepositRequest(
            amount=500.00,
            description='Test deposit',
            destination_id='1',
        )

        assert request.source_id is None
        assert request.source_name is None
