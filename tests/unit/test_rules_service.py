"""Unit tests for RuleService."""

from datetime import date
from unittest.mock import AsyncMock

import pytest

from lampyrid.models.firefly_models import (
    Meta,
    ObjectLink,
    PageLink,
    Pagination,
    RuleAction,
    RuleActionKeyword,
    RuleArray,
    RuleRead,
    RuleSingle,
    RuleTrigger,
    RuleTriggerKeyword,
    RuleTriggerType,
    TransactionArray,
)
from lampyrid.models.firefly_models import (
    Rule as RuleAttrs,
)
from lampyrid.models.lampyrid_models import (
    ExecuteRuleRequest,
    GetRuleRequest,
    SearchRulesRequest,
    TestRuleRequest,
    UpdateRuleRequest,
)
from lampyrid.services.rules import RuleService


def _make_rule_attrs(
    title: str = 'Test Rule',
    description: str = 'Test Description',
    active: bool = True,
    strict: bool = True,
    stop_processing: bool = False,
    trigger_type: str = 'description_contains',
    trigger_value: str = 'test',
    action_type: str = 'set_category',
    action_value: str = 'Test Category',
) -> RuleAttrs:
    """Create RuleAttrs for testing."""
    return RuleAttrs(
        title=title,
        description=description,
        rule_group_id='1',
        active=active,
        strict=strict,
        stop_processing=stop_processing,
        trigger=RuleTriggerType('store-journal'),
        triggers=[
            RuleTrigger(
                type=RuleTriggerKeyword(trigger_type),
                value=trigger_value,
                prohibited=False,
                active=True,
            )
        ],
        actions=[
            RuleAction(
                type=RuleActionKeyword(action_type),
                value=action_value,
                active=True,
            )
        ],
    )


def _make_rule_read(
    rule_id: str = '1',
    title: str = 'Test Rule',
    **attrs_kwargs,
) -> RuleRead:
    """Create RuleRead for testing."""
    return RuleRead(
        type='rules',
        id=rule_id,
        attributes=_make_rule_attrs(title=title, **attrs_kwargs),
        links=ObjectLink(self='http://example.com'),
    )


def _make_rule_array(rules: list[RuleRead]) -> RuleArray:
    """Create RuleArray with pagination."""
    return RuleArray(
        data=rules,
        meta=Meta(
            pagination=Pagination(
                total=len(rules),
                count=len(rules),
                per_page=50,
                current_page=1,
                total_pages=1,
            )
        ),
        links=PageLink(
            self='http://example.com',
            first='http://example.com?page=1',
            last='http://example.com?page=1',
        ),
    )


class TestRuleService:
    """Test cases for RuleService class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock FireflyClient."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_client):
        """Create a RuleService with mocked client."""
        return RuleService(mock_client)

    @pytest.mark.asyncio
    async def test_search_rules_by_title_contains(self, service, mock_client):
        """Test searching rules by title contains."""
        rule1 = _make_rule_read('1', 'Auto-categorize groceries')
        rule2 = _make_rule_read('2', 'Manual invoice processing')
        mock_client.get_rules.return_value = _make_rule_array([rule1, rule2])

        req = SearchRulesRequest(title_contains='auto')
        result = await service.search_rules(req)

        assert len(result) == 1
        assert result[0].title == 'Auto-categorize groceries'

    @pytest.mark.asyncio
    async def test_search_rules_by_active_status(self, service, mock_client):
        """Test searching rules by active status."""
        rule1 = _make_rule_read('1', 'Active Rule', active=True)
        rule2 = _make_rule_read('2', 'Inactive Rule', active=False)
        mock_client.get_rules.return_value = _make_rule_array([rule1, rule2])

        req = SearchRulesRequest(active=True)
        result = await service.search_rules(req)

        assert len(result) == 1
        assert result[0].title == 'Active Rule'

    @pytest.mark.asyncio
    async def test_search_rules_by_trigger_type(self, service, mock_client):
        """Test searching rules by trigger type keyword."""
        rule1 = _make_rule_read(
            '1',
            'Description Trigger',
            trigger_type='description_contains',
        )
        rule2 = _make_rule_read('2', 'Amount Trigger', trigger_type='amount_greater_than')
        mock_client.get_rules.return_value = _make_rule_array([rule1, rule2])

        req = SearchRulesRequest(trigger_type='description')
        result = await service.search_rules(req)

        assert len(result) == 1
        assert result[0].title == 'Description Trigger'

    @pytest.mark.asyncio
    async def test_search_rules_by_action_type(self, service, mock_client):
        """Test searching rules by action type keyword."""
        rule1 = _make_rule_read(
            '1',
            'Set Budget Rule',
            action_type='set_budget',
        )
        rule2 = _make_rule_read('2', 'Set Category Rule', action_type='set_category')
        mock_client.get_rules.return_value = _make_rule_array([rule1, rule2])

        req = SearchRulesRequest(action_type='budget')
        result = await service.search_rules(req)

        assert len(result) == 1
        assert result[0].title == 'Set Budget Rule'

    @pytest.mark.asyncio
    async def test_search_rules_by_trigger_value_pattern(self, service, mock_client):
        """Test searching rules by trigger value regex pattern."""
        rule1 = _make_rule_read(
            '1',
            'Groceries Rule',
            trigger_value='groceries',
        )
        rule2 = _make_rule_read('2', 'Utilities Rule', trigger_value='utilities')
        mock_client.get_rules.return_value = _make_rule_array([rule1, rule2])

        req = SearchRulesRequest(trigger_value_pattern='.*groceries.*')
        result = await service.search_rules(req)

        assert len(result) == 1
        assert result[0].title == 'Groceries Rule'

    @pytest.mark.asyncio
    async def test_search_rules_by_action_value_pattern(self, service, mock_client):
        """Test searching rules by action value regex pattern."""
        rule1 = _make_rule_read(
            '1',
            'Budget 100 Rule',
            action_value='100.00',
        )
        rule2 = _make_rule_read('2', 'Budget Text Rule', action_value='Food')
        mock_client.get_rules.return_value = _make_rule_array([rule1, rule2])

        req = SearchRulesRequest(action_value_pattern='^[0-9]+')
        result = await service.search_rules(req)

        assert len(result) == 1
        assert result[0].title == 'Budget 100 Rule'

    @pytest.mark.asyncio
    async def test_search_rules_invalid_regex_trigger(self, service, mock_client):
        """Test that invalid trigger regex pattern raises ValueError."""
        mock_client.get_rules.return_value = _make_rule_array([])

        req = SearchRulesRequest(trigger_value_pattern='[invalid')
        with pytest.raises(ValueError, match='Invalid trigger_value_pattern regex'):
            await service.search_rules(req)

    @pytest.mark.asyncio
    async def test_search_rules_invalid_regex_action(self, service, mock_client):
        """Test that invalid action regex pattern raises ValueError."""
        mock_client.get_rules.return_value = _make_rule_array([])

        req = SearchRulesRequest(action_value_pattern='[invalid')
        with pytest.raises(ValueError, match='Invalid action_value_pattern regex'):
            await service.search_rules(req)

    @pytest.mark.asyncio
    async def test_search_rules_with_pagination(self, service, mock_client):
        """Test that search handles pagination correctly."""
        rule1 = _make_rule_read('1', 'Rule 1')
        rule2 = _make_rule_read('2', 'Rule 2')

        # Create paginated responses
        page1_response = RuleArray(
            data=[rule1],
            meta=Meta(
                pagination=Pagination(
                    total=2,
                    count=1,
                    per_page=1,
                    current_page=1,
                    total_pages=2,
                )
            ),
            links=PageLink(
                self='http://example.com?page=1',
                first='http://example.com?page=1',
                last='http://example.com?page=2',
            ),
        )
        page2_response = RuleArray(
            data=[rule2],
            meta=Meta(
                pagination=Pagination(
                    total=2,
                    count=1,
                    per_page=1,
                    current_page=2,
                    total_pages=2,
                )
            ),
            links=PageLink(
                self='http://example.com?page=2',
                first='http://example.com?page=1',
                last='http://example.com?page=2',
            ),
        )

        mock_client.get_rules.side_effect = [page1_response, page2_response]

        req = SearchRulesRequest(active=True)
        result = await service.search_rules(req)

        assert len(result) == 2
        assert result[0].title == 'Rule 1'
        assert result[1].title == 'Rule 2'
        assert mock_client.get_rules.call_count == 2

    @pytest.mark.asyncio
    async def test_search_rules_with_none_pagination(self, service, mock_client):
        """Test that search handles None pagination metadata."""
        rule1 = _make_rule_read('1', 'Rule 1')
        response = RuleArray(
            data=[rule1],
            meta=Meta(pagination=None),
            links=PageLink(
                self='http://example.com',
                first='http://example.com',
                last='http://example.com',
            ),
        )
        mock_client.get_rules.return_value = response

        req = SearchRulesRequest(active=True)
        result = await service.search_rules(req)

        assert len(result) == 1
        assert result[0].title == 'Rule 1'

    @pytest.mark.asyncio
    async def test_get_rule(self, service, mock_client):
        """Test getting a single rule by ID."""
        rule_read = _make_rule_read('42', 'My Rule')
        rule_single = RuleSingle(data=rule_read)
        mock_client.get_rule.return_value = rule_single

        req = GetRuleRequest(id='42')
        result = await service.get_rule(req)

        assert result.id == '42'
        assert result.title == 'My Rule'
        assert len(result.triggers) == 1
        assert len(result.actions) == 1
        mock_client.get_rule.assert_called_once_with('42')

    @pytest.mark.asyncio
    async def test_update_rule_basic_fields(self, service, mock_client):
        """Test updating basic rule fields."""
        rule_read = _make_rule_read('42', 'Updated Rule', active=False)
        rule_single = RuleSingle(data=rule_read)
        mock_client.update_rule.return_value = rule_single

        req = UpdateRuleRequest(
            rule_id='42',
            title='Updated Rule',
            active=False,
        )
        result = await service.update_rule(req)

        assert result.id == '42'
        assert result.title == 'Updated Rule'
        assert result.active is False
        mock_client.update_rule.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_rule_with_triggers(self, service, mock_client):
        """Test updating rule with new triggers."""
        rule_read = _make_rule_read('42', 'Rule with New Triggers')
        rule_single = RuleSingle(data=rule_read)
        mock_client.update_rule.return_value = rule_single

        req = UpdateRuleRequest(
            rule_id='42',
            triggers=[
                {'type': 'description_contains', 'value': 'groceries'},
            ],
        )
        result = await service.update_rule(req)

        assert result.id == '42'
        mock_client.update_rule.assert_called_once()

        # Check the call to verify triggers were converted
        call_args = mock_client.update_rule.call_args
        rule_update = call_args[0][1]
        assert rule_update.triggers is not None
        assert len(rule_update.triggers) == 1

    @pytest.mark.asyncio
    async def test_update_rule_invalid_trigger_dict(self, service, mock_client):
        """Test that invalid trigger dict raises ValueError."""
        req = UpdateRuleRequest(
            rule_id='42',
            triggers=[
                {'invalid_field': 'value'},  # Missing 'type'
            ],
        )
        with pytest.raises(ValueError, match='Invalid trigger format'):
            await service.update_rule(req)

    @pytest.mark.asyncio
    async def test_update_rule_invalid_action_dict(self, service, mock_client):
        """Test that invalid action dict raises ValueError."""
        req = UpdateRuleRequest(
            rule_id='42',
            actions=[
                {'invalid_field': 'value'},  # Missing 'type'
            ],
        )
        with pytest.raises(ValueError, match='Invalid action format'):
            await service.update_rule(req)

    @pytest.mark.asyncio
    async def test_test_rule(self, service, mock_client):
        """Test the test_rule method (preview mode)."""
        rule_single = RuleSingle(data=_make_rule_read('42', 'Test Rule'))
        mock_client.get_rule.return_value = rule_single

        # Mock empty transaction array
        mock_client.test_rule.return_value = TransactionArray(
            data=[],
            meta=Meta(
                pagination=Pagination(
                    total=0,
                    count=0,
                    per_page=50,
                    current_page=1,
                    total_pages=1,
                )
            ),
            links=PageLink(
                self='http://example.com',
                first='http://example.com',
                last='http://example.com',
            ),
        )

        req = TestRuleRequest(
            rule_id='42',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        result = await service.test_rule(req)

        assert result.rule_id == '42'
        assert result.rule_title == 'Test Rule'
        assert result.matched_transaction_count == 0
        assert result.matched_transactions == []
        mock_client.get_rule.assert_called_once_with('42')
        mock_client.test_rule.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_rule_without_confirm(self, service, mock_client):
        """Test that execute_rule without confirm=True raises ValueError."""
        req = ExecuteRuleRequest(
            rule_id='42',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            confirm=False,
        )
        with pytest.raises(ValueError, match='confirm=True'):
            await service.execute_rule(req)

    @pytest.mark.asyncio
    async def test_execute_rule_with_confirm(self, service, mock_client):
        """Test executing a rule with proper confirmation."""
        rule_single = RuleSingle(data=_make_rule_read('42', 'Execute Rule'))
        mock_client.get_rule.return_value = rule_single
        mock_client.trigger_rule.return_value = True

        req = ExecuteRuleRequest(
            rule_id='42',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            confirm=True,
        )
        result = await service.execute_rule(req)

        assert result.rule_id == '42'
        assert result.rule_title == 'Execute Rule'
        assert result.success is True
        assert 'asynchronously' in result.message
        mock_client.get_rule.assert_called_once_with('42')
        mock_client.trigger_rule.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_rules_no_criteria(self):
        """Test that search_rules without any criteria raises ValueError."""
        with pytest.raises(ValueError, match='At least one search criterion'):
            SearchRulesRequest()
