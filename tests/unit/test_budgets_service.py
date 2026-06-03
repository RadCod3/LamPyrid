"""Unit tests for BudgetService."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lampyrid.models.lampyrid_models import (
    CreateBudgetRequest,
    DeleteBudgetLimitRequest,
    GetAvailableBudgetRequest,
    GetBudgetSpendingRequest,
    GetBudgetSummaryRequest,
    ListBudgetLimitsRequest,
    SetBudgetLimitRequest,
)
from lampyrid.services.budgets import BudgetService


def _make_limit_read(
    limit_id: str,
    budget_id: str,
    start: date,
    end: date,
    amount: str | None = '100.0',
    spent_sums: list[str] | None = None,
    currency_code: str | None = 'USD',
    notes: str | None = None,
):
    """Build a mock BudgetLimitRead with date-returning start/end and spent entries."""
    spent = None
    if spent_sums is not None:
        spent = [MagicMock(sum=value) for value in spent_sums]

    start_mock = MagicMock()
    start_mock.date.return_value = start
    end_mock = MagicMock()
    end_mock.date.return_value = end

    return MagicMock(
        id=limit_id,
        attributes=MagicMock(
            budget_id=budget_id,
            start=start_mock,
            end=end_mock,
            amount=amount,
            spent=spent,
            currency_code=currency_code,
            notes=notes,
        ),
    )


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

        budget_req = CreateBudgetRequest(name='New Budget', active=True, notes='Test notes')

        result = await service.create_budget(budget_req)

        # Verify the client was called
        # The service creates a BudgetStore internal to create_budgets
        mock_client.create_budget.assert_called_once()
        args, _ = mock_client.create_budget.call_args
        assert args[0].name == 'New Budget'
        assert args[0].active is True
        assert args[0].notes == 'Test notes'

        # Verify the result is converted correctly
        assert result.id == '123'
        assert result.name == 'New Budget'
        assert result.active is True

    # =========================================================================
    # Budget Limit Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_set_budget_limit_creates_when_none_exists(self, mock_service):
        """set_budget_limit POSTs a new limit when none exists for the period."""
        service, mock_client = mock_service

        # No existing limit for the period
        empty = MagicMock()
        empty.data = []
        mock_client.get_budget_limits.return_value = empty

        created = MagicMock()
        created.data = _make_limit_read('7', '3', date(2026, 6, 1), date(2026, 6, 30), '500.0')
        mock_client.create_budget_limit.return_value = created

        req = SetBudgetLimitRequest(
            budget_id='3',
            amount=500.0,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
            currency_code='USD',
        )
        result = await service.set_budget_limit(req)

        mock_client.create_budget_limit.assert_called_once()
        mock_client.update_budget_limit.assert_not_called()
        budget_id_arg, store_arg = mock_client.create_budget_limit.call_args[0]
        assert budget_id_arg == '3'
        assert store_arg.budget_id == '3'
        assert store_arg.amount == '500.0'
        assert store_arg.start == date(2026, 6, 1)
        assert store_arg.end == date(2026, 6, 30)
        assert store_arg.currency_code == 'USD'

        assert result.id == '7'
        assert result.budget_id == '3'
        assert result.amount == 500.0

    @pytest.mark.asyncio
    async def test_set_budget_limit_updates_when_exists(self, mock_service):
        """set_budget_limit PUTs the existing limit when one matches the period."""
        service, mock_client = mock_service

        existing = MagicMock()
        existing.data = [_make_limit_read('9', '3', date(2026, 6, 1), date(2026, 6, 30), '100.0')]
        mock_client.get_budget_limits.return_value = existing

        updated = MagicMock()
        updated.data = _make_limit_read('9', '3', date(2026, 6, 1), date(2026, 6, 30), '650.0')
        mock_client.update_budget_limit.return_value = updated

        req = SetBudgetLimitRequest(
            budget_id='3',
            amount=650.0,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
        )
        result = await service.set_budget_limit(req)

        mock_client.update_budget_limit.assert_called_once()
        mock_client.create_budget_limit.assert_not_called()
        budget_id_arg, limit_id_arg, update_arg = mock_client.update_budget_limit.call_args[0]
        assert budget_id_arg == '3'
        assert limit_id_arg == '9'
        assert update_arg.amount == '650.0'

        assert result.amount == 650.0

    @pytest.mark.asyncio
    async def test_set_budget_limit_defaults_to_current_month(self, mock_service):
        """set_budget_limit uses the current calendar month when dates are omitted."""
        service, mock_client = mock_service

        empty = MagicMock()
        empty.data = []
        mock_client.get_budget_limits.return_value = empty

        today = date.today()
        first = today.replace(day=1)
        last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        created = MagicMock()
        created.data = _make_limit_read('7', '3', first, last, '300.0')
        mock_client.create_budget_limit.return_value = created

        req = SetBudgetLimitRequest(budget_id='3', amount=300.0)
        await service.set_budget_limit(req)

        # Period passed to the lookup should be the current month
        _, lookup_start, lookup_end = mock_client.get_budget_limits.call_args[0]
        assert lookup_start == first
        assert lookup_end == last

    @pytest.mark.asyncio
    async def test_set_budget_limit_resolves_budget_name(self, mock_service):
        """set_budget_limit resolves a budget_name to its ID before creating a limit."""
        service, mock_client = mock_service

        rent = MagicMock(id='1')
        rent.attributes.name = 'Rent'
        groceries = MagicMock(id='3')
        groceries.attributes.name = 'Groceries'
        budgets = MagicMock()
        budgets.data = [rent, groceries]
        mock_client.get_budgets.return_value = budgets

        empty = MagicMock()
        empty.data = []
        mock_client.get_budget_limits.return_value = empty

        created = MagicMock()
        created.data = _make_limit_read('7', '3', date(2026, 6, 1), date(2026, 6, 30), '500.0')
        mock_client.create_budget_limit.return_value = created

        req = SetBudgetLimitRequest(
            budget_name='groceries',
            amount=500.0,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
        )
        await service.set_budget_limit(req)

        budget_id_arg, _ = mock_client.create_budget_limit.call_args[0]
        assert budget_id_arg == '3'

    @pytest.mark.asyncio
    async def test_resolve_budget_name_not_found_raises(self, mock_service):
        """Resolving an unknown budget name raises a clear ValueError."""
        service, mock_client = mock_service

        rent = MagicMock(id='1')
        rent.attributes.name = 'Rent'
        budgets = MagicMock()
        budgets.data = [rent]
        mock_client.get_budgets.return_value = budgets

        req = ListBudgetLimitsRequest(budget_name='Nonexistent')
        with pytest.raises(ValueError, match='No budget found'):
            await service.list_budget_limits(req)

    @pytest.mark.asyncio
    async def test_list_budget_limits_maps_results(self, mock_service):
        """list_budget_limits maps the array to BudgetLimit models, parsing spent."""
        service, mock_client = mock_service

        limits = MagicMock()
        limits.data = [
            _make_limit_read(
                '7', '3', date(2026, 6, 1), date(2026, 6, 30), '500.0', spent_sums=['-120.0']
            ),
            _make_limit_read(
                '8', '3', date(2026, 7, 1), date(2026, 7, 31), '400.0', spent_sums=None
            ),
        ]
        mock_client.get_budget_limits.return_value = limits

        req = ListBudgetLimitsRequest(budget_id='3')
        result = await service.list_budget_limits(req)

        assert len(result) == 2
        assert result[0].id == '7'
        assert result[0].amount == 500.0
        assert result[0].spent == 120.0  # abs of -120.0
        assert result[1].id == '8'
        assert result[1].spent is None

    @pytest.mark.asyncio
    async def test_delete_budget_limit_found(self, mock_service):
        """delete_budget_limit deletes the matching limit and returns True."""
        service, mock_client = mock_service

        existing = MagicMock()
        existing.data = [_make_limit_read('9', '3', date(2026, 6, 1), date(2026, 6, 30), '100.0')]
        mock_client.get_budget_limits.return_value = existing
        mock_client.delete_budget_limit.return_value = True

        req = DeleteBudgetLimitRequest(
            budget_id='3', start_date=date(2026, 6, 1), end_date=date(2026, 6, 30)
        )
        result = await service.delete_budget_limit(req)

        assert result is True
        mock_client.delete_budget_limit.assert_called_once_with('3', '9')

    @pytest.mark.asyncio
    async def test_delete_budget_limit_not_found_raises(self, mock_service):
        """delete_budget_limit raises ValueError when no limit exists for the period."""
        service, mock_client = mock_service

        empty = MagicMock()
        empty.data = []
        mock_client.get_budget_limits.return_value = empty

        req = DeleteBudgetLimitRequest(
            budget_id='3', start_date=date(2026, 6, 1), end_date=date(2026, 6, 30)
        )
        with pytest.raises(ValueError, match='No budget limit set'):
            await service.delete_budget_limit(req)
        mock_client.delete_budget_limit.assert_not_called()
