"""Unit tests for BudgetService."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lampyrid.models.lampyrid_models import (
    GetAvailableBudgetRequest,
    GetBudgetSpendingRequest,
    GetBudgetSummaryRequest,
)
from lampyrid.services.budgets import BudgetService


class TestBudgetService:
    """Test cases for BudgetService class."""

    @pytest.fixture
    def mock_service(self):
        """Create a BudgetService with mocked FireflyClient."""
        with patch('lampyrid.services.budgets.FireflyClient') as mock_firefly:
            mock_client_instance = AsyncMock()
            mock_firefly.return_value = mock_client_instance

            service = BudgetService(mock_client_instance)
            return service, mock_client_instance

    @pytest.mark.asyncio
    async def test_get_budget_spending_with_spent_entries(self, mock_service):
        """Test get_budget_spending when spent entries exist."""
        service, mock_client = mock_service

        # Mock response with spent entries
        mock_budget_single = MagicMock()
        mock_budget_single.data.id = '1'
        mock_budget_single.data.attributes.name = 'Test Budget'

        mock_limits_response = MagicMock()
        mock_limits_response.data = [
            MagicMock(
                attributes=MagicMock(
                    spent=[MagicMock(sum='50.0'), MagicMock(sum='25.0')], amount='200.0'
                )
            )
        ]

        mock_client.get_budget.return_value = mock_budget_single
        mock_client.get_budget_limits.return_value = mock_limits_response

        req = GetBudgetSpendingRequest(
            budget_id='1', start_date=date(2023, 1, 1), end_date=date(2023, 12, 31)
        )

        result = await service.get_budget_spending(req)

        # Verify calculations
        assert result.budget_id == '1'
        assert result.budget_name == 'Test Budget'
        assert result.spent == 75.0  # 50.0 + 25.0
        assert result.budgeted == 200.0
        assert result.remaining == 125.0
        assert result.percentage_spent == 37.5  # (75.0 / 200.0) * 100

    @pytest.mark.asyncio
    async def test_get_budget_spending_without_spent_entries(self, mock_service):
        """Test get_budget_spending when no spent entries exist."""
        service, mock_client = mock_service

        # Mock response without spent entries but with amount
        mock_budget_single = MagicMock()
        mock_budget_single.data.id = '1'
        mock_budget_single.data.attributes.name = 'Test Budget'

        mock_limits_response = MagicMock()
        mock_limits_response.data = [MagicMock(attributes=MagicMock(spent=None, amount='150.0'))]

        mock_client.get_budget.return_value = mock_budget_single
        mock_client.get_budget_limits.return_value = mock_limits_response

        req = GetBudgetSpendingRequest(
            budget_id='1', start_date=date(2023, 1, 1), end_date=date(2023, 12, 31)
        )

        result = await service.get_budget_spending(req)

        # Verify calculations
        assert result.budget_id == '1'
        assert result.budget_name == 'Test Budget'
        assert result.spent == 0.0
        assert result.budgeted == 150.0
        assert result.remaining == 150.0
        assert result.percentage_spent == 0.0

    @pytest.mark.asyncio
    async def test_get_budget_spending_without_amount(self, mock_service):
        """Test get_budget_spending when no amount is set."""
        service, mock_client = mock_service

        # Mock response with spent entries but no amount
        mock_budget_single = MagicMock()
        mock_budget_single.data.id = '1'
        mock_budget_single.data.attributes.name = 'Test Budget'

        mock_limits_response = MagicMock()
        mock_limits_response.data = [
            MagicMock(attributes=MagicMock(spent=[MagicMock(sum='30.0')], amount=None))
        ]

        mock_client.get_budget.return_value = mock_budget_single
        mock_client.get_budget_limits.return_value = mock_limits_response

        req = GetBudgetSpendingRequest(
            budget_id='1', start_date=date(2023, 1, 1), end_date=date(2023, 12, 31)
        )

        result = await service.get_budget_spending(req)

        # Verify calculations when no amount is set
        assert result.budget_id == '1'
        assert result.budget_name == 'Test Budget'
        assert result.spent == 30.0
        assert result.budgeted is None
        assert result.remaining is None
        assert result.percentage_spent is None

    @pytest.mark.asyncio
    async def test_get_budget_summary_with_budgeted_amounts(self, mock_service):
        """Test get_budget_summary when budgets have budgeted amounts."""
        service, mock_client = mock_service

        # Mock budgets response
        mock_budgets_response = MagicMock()
        mock_budgets_response.data = [MagicMock(id='1'), MagicMock(id='2')]

        # Mock individual budget spending calls
        async def mock_get_budget_limits(budget_id, start_date, end_date):
            if budget_id == '1':
                mock_response = MagicMock()
                mock_response.data = [
                    MagicMock(
                        attributes=MagicMock(
                            spent=[MagicMock(sum='50.0'), MagicMock(sum='0.0')], amount='100.0'
                        )
                    )
                ]
                return mock_response
            else:
                mock_response = MagicMock()
                mock_response.data = [
                    MagicMock(
                        attributes=MagicMock(
                            spent=[MagicMock(sum='25.0'), MagicMock(sum='0.0')], amount='50.0'
                        )
                    )
                ]
                return mock_response

        # Mock individual budget calls for budget names
        def mock_get_budget(budget_id):
            mock_budget = MagicMock()
            if budget_id == '1':
                mock_budget.data.attributes.name = 'Budget 1'
            else:
                mock_budget.data.attributes.name = 'Budget 2'
            return mock_budget

        mock_client.get_budgets.return_value = mock_budgets_response
        mock_client.get_budget.side_effect = mock_get_budget
        mock_client.get_budget_limits.side_effect = mock_get_budget_limits

        req = GetBudgetSummaryRequest(start_date=date(2023, 1, 1), end_date=date(2023, 12, 31))

        result = await service.get_budget_summary(req)

        # Verify summary calculations
        assert len(result.budgets) == 2
        assert result.total_spent == 75.0  # 50.0 + 25.0
        assert result.total_budgeted == 150.0  # 100.0 + 50.0
        assert result.total_remaining == 75.0
        assert result.available_budget is None

    @pytest.mark.asyncio
    async def test_get_budget_summary_without_budgeted_amounts(self, mock_service):
        """Test get_budget_summary when budgets have no budgeted amounts."""
        service, mock_client = mock_service

        # Mock budgets response
        mock_budgets_response = MagicMock()
        mock_budgets_response.data = [MagicMock(id='1'), MagicMock(id='2')]

        # Mock individual budget spending with no budgeted amounts
        async def mock_get_budget_limits(budget_id, start_date, end_date):
            if budget_id == '1':
                mock_response = MagicMock()
                mock_response.data = [
                    MagicMock(attributes=MagicMock(spent=[MagicMock(sum='30.0')], amount=None))
                ]
                return mock_response
            else:
                mock_response = MagicMock()
                mock_response.data = [
                    MagicMock(attributes=MagicMock(spent=[MagicMock(sum='20.0')], amount=None))
                ]
                return mock_response

        # Mock individual budget calls for budget names
        def mock_get_budget(budget_id):
            mock_budget = MagicMock()
            if budget_id == '1':
                mock_budget.data.attributes.name = 'Budget 1'
            else:
                mock_budget.data.attributes.name = 'Budget 2'
            return mock_budget

        mock_client.get_budgets.return_value = mock_budgets_response
        mock_client.get_budget.side_effect = mock_get_budget
        mock_client.get_budget_limits.side_effect = mock_get_budget_limits

        req = GetBudgetSummaryRequest(start_date=date(2023, 1, 1), end_date=date(2023, 12, 31))

        result = await service.get_budget_summary(req)

        # Verify summary calculations
        assert len(result.budgets) == 2
        assert result.total_spent == 50.0  # 30.0 + 20.0
        assert result.total_budgeted is None
        assert result.total_remaining is None
        assert result.available_budget is None

    @pytest.mark.asyncio
    async def test_get_available_budget_with_data(self, mock_service):
        """Test get_available_budget when data is available."""
        service, mock_client = mock_service

        # Mock available budgets response
        mock_available_response = MagicMock()
        mock_budget = MagicMock()
        mock_budget.attributes.amount = '500.0'
        mock_budget.attributes.currency_code = 'USD'
        mock_budget.attributes.start = MagicMock()
        mock_budget.attributes.start.date.return_value = date(2023, 1, 1)
        mock_budget.attributes.end = MagicMock()
        mock_budget.attributes.end.date.return_value = date(2023, 12, 31)

        mock_available_response.data = [mock_budget]

        mock_client.get_available_budgets.return_value = mock_available_response

        req = GetAvailableBudgetRequest(start_date=date(2023, 1, 1), end_date=date(2023, 12, 31))

        result = await service.get_available_budget(req)

        # Verify result with available data
        assert result.amount == 500.0
        assert result.currency_code == 'USD'
        assert result.start_date == date(2023, 1, 1)
        assert result.end_date == date(2023, 12, 31)

    @pytest.mark.asyncio
    async def test_get_available_budget_without_data(self, mock_service):
        """Test get_available_budget when no data is available."""
        service, mock_client = mock_service

        # Mock empty available budgets response
        mock_available_response = MagicMock()
        mock_available_response.data = []

        mock_client.get_available_budgets.return_value = mock_available_response

        req = GetAvailableBudgetRequest(start_date=date(2023, 1, 1), end_date=date(2023, 12, 31))

        result = await service.get_available_budget(req)

        # Verify default result when no data
        assert result.amount == 0.0
        assert result.currency_code == 'USD'
        assert result.start_date == date(2023, 1, 1)
        assert result.end_date == date(2023, 12, 31)

    @pytest.mark.asyncio
    async def test_get_available_budget_uses_default_dates(self, mock_service):
        """Test get_available_budget uses default dates when not provided."""
        service, mock_client = mock_service

        # Mock empty available budgets response
        mock_available_response = MagicMock()
        mock_available_response.data = []

        mock_client.get_available_budgets.return_value = mock_available_response

        # Request with no dates
        req = GetAvailableBudgetRequest()

        result = await service.get_available_budget(req)

        # Verify default dates are used
        today = date.today()
        assert result.start_date == today.replace(day=1)
        assert result.end_date == today

    @pytest.mark.asyncio
    async def test_create_budget(self, mock_service):
        """Test creating a new budget."""
        service, mock_client = mock_service

        # Mock response
        mock_budget_single = MagicMock()
        mock_budget_single.data.id = '123'
        mock_budget_single.data.attributes.name = 'New Budget'
        mock_budget_single.data.attributes.active = True
        mock_budget_single.data.attributes.notes = None
        mock_budget_single.data.attributes.order = 0

        mock_client.create_budget.return_value = mock_budget_single

        # Mock BudgetStore to avoid complex required fields
        budget_store = MagicMock()

        result = await service.create_budget(budget_store)

        # Verify the client was called
        mock_client.create_budget.assert_called_once_with(budget_store)

        # Verify the result is converted correctly
        assert result.id == '123'
        assert result.name == 'New Budget'
        assert result.active is True
