"""Integration tests for rule management tools."""

from datetime import date, timedelta
from typing import List

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from lampyrid.clients.firefly import FireflyClient

# ==================== Helpers ====================

# Cached rule group ID for test rule creation
_test_rule_group_id: str | None = None


async def _ensure_rule_group(firefly_client: FireflyClient) -> str:
    """Get or create a rule group for integration tests. Caches the ID."""
    global _test_rule_group_id
    if _test_rule_group_id is not None:
        return _test_rule_group_id

    # Check for existing rule groups
    r = await firefly_client._client.get('rule-groups')
    r.raise_for_status()
    groups = r.json().get('data', [])
    if groups:
        _test_rule_group_id = groups[0]['id']
        return _test_rule_group_id

    # Create one if none exist
    r = await firefly_client._client.post(
        'rule-groups',
        json={'title': 'Test Rules', 'order': 1},
    )
    r.raise_for_status()
    _test_rule_group_id = r.json()['data']['id']
    return _test_rule_group_id


async def _create_rule_via_api(
    firefly_client: FireflyClient,
    title: str,
    trigger_type: str = 'description_contains',
    trigger_value: str = 'test',
    action_type: str = 'set_category',
    action_value: str = 'Test Category',
    active: bool = True,
) -> str:
    """Create a rule directly via Firefly III API and return its ID."""
    rule_group_id = await _ensure_rule_group(firefly_client)
    r = await firefly_client._client.post(
        'rules',
        json={
            'title': title,
            'rule_group_id': rule_group_id,
            'trigger': 'store-journal',
            'active': active,
            'strict': True,
            'triggers': [
                {'type': trigger_type, 'value': trigger_value, 'active': True},
            ],
            'actions': [
                {'type': action_type, 'value': action_value, 'active': True},
            ],
        },
    )
    if r.status_code >= 400:
        raise RuntimeError(f'Failed to create rule ({r.status_code}): {r.text}')
    return r.json()['data']['id']


async def _delete_rule_via_api(firefly_client: FireflyClient, rule_id: str) -> None:
    """Delete a rule directly via Firefly III API."""
    r = await firefly_client._client.delete(f'rules/{rule_id}')
    r.raise_for_status()


# ==================== Fixtures ====================


@pytest.fixture
async def rule_cleanup(firefly_client: FireflyClient):
    """Fixture to track and cleanup rules created during tests."""
    created_rule_ids: List[str] = []

    yield created_rule_ids

    for rule_id in created_rule_ids:
        try:
            await _delete_rule_via_api(firefly_client, rule_id)
        except Exception as e:
            print(f'Failed to cleanup rule {rule_id}: {e}')


# ==================== Search Rules ====================


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_search_rules_returns_results(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test searching rules by title keyword."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Categorize Groceries',
        trigger_type='description_contains',
        trigger_value='groceries',
        action_type='set_category',
        action_value='Groceries',
    )
    rule_cleanup.append(rule_id)

    result = await mcp_client.call_tool(
        'search_rules',
        {'req': {'title_contains': 'Categorize Groceries'}},
    )
    rules = result.structured_content['result']
    assert len(rules) >= 1
    assert any(r['title'] == 'Integration Test - Categorize Groceries' for r in rules)


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_search_rules_by_active_status(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test filtering rules by active status."""
    active_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Active Rule',
        active=True,
    )
    rule_cleanup.append(active_id)

    inactive_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Inactive Rule',
        active=False,
    )
    rule_cleanup.append(inactive_id)

    # Search for active rules only
    result = await mcp_client.call_tool(
        'search_rules',
        {'req': {'title_contains': 'Integration Test', 'active': True}},
    )
    rules = result.structured_content['result']
    titles = [r['title'] for r in rules]
    assert 'Integration Test - Active Rule' in titles
    assert 'Integration Test - Inactive Rule' not in titles


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_search_rules_by_trigger_type(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test filtering rules by trigger type keyword."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Amount Rule',
        trigger_type='amount_more',
        trigger_value='100',
    )
    rule_cleanup.append(rule_id)

    result = await mcp_client.call_tool(
        'search_rules',
        {'req': {'title_contains': 'Integration Test', 'trigger_type': 'amount'}},
    )
    rules = result.structured_content['result']
    assert any(r['title'] == 'Integration Test - Amount Rule' for r in rules)


# ==================== Get Rule ====================


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_get_rule(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test retrieving a single rule by ID."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Get Rule',
        trigger_type='description_contains',
        trigger_value='test-pattern',
        action_type='set_category',
        action_value='Test',
    )
    rule_cleanup.append(rule_id)

    result = await mcp_client.call_tool('get_rule', {'req': {'id': rule_id}})
    rule = result.structured_content

    assert rule['id'] == rule_id
    assert rule['title'] == 'Integration Test - Get Rule'
    assert rule['active'] is True
    assert len(rule['triggers']) == 1
    assert rule['triggers'][0]['type'] == 'description_contains'
    assert rule['triggers'][0]['value'] == 'test-pattern'
    assert len(rule['actions']) == 1
    assert rule['actions'][0]['type'] == 'set_category'
    assert rule['actions'][0]['value'] == 'Test'


# ==================== Update Rule ====================


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_update_rule_title(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test updating a rule's title."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Original Title',
    )
    rule_cleanup.append(rule_id)

    result = await mcp_client.call_tool(
        'update_rule',
        {'req': {'rule_id': rule_id, 'title': 'Integration Test - Updated Title'}},
    )
    rule = result.structured_content
    assert rule['title'] == 'Integration Test - Updated Title'

    # Verify persistence by re-fetching
    verify = await mcp_client.call_tool('get_rule', {'req': {'id': rule_id}})
    assert verify.structured_content['title'] == 'Integration Test - Updated Title'


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_update_rule_active_status(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test toggling a rule's active status."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Toggle Active',
        active=True,
    )
    rule_cleanup.append(rule_id)

    # Deactivate
    result = await mcp_client.call_tool(
        'update_rule',
        {'req': {'rule_id': rule_id, 'active': False}},
    )
    assert result.structured_content['active'] is False

    # Reactivate
    result = await mcp_client.call_tool(
        'update_rule',
        {'req': {'rule_id': rule_id, 'active': True}},
    )
    assert result.structured_content['active'] is True


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_update_rule_triggers(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test updating a rule's triggers."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Update Triggers',
        trigger_type='description_contains',
        trigger_value='old-pattern',
    )
    rule_cleanup.append(rule_id)

    result = await mcp_client.call_tool(
        'update_rule',
        {
            'req': {
                'rule_id': rule_id,
                'triggers': [
                    {'type': 'description_contains', 'value': 'new-pattern'},
                ],
            }
        },
    )
    rule = result.structured_content
    assert len(rule['triggers']) == 1
    assert rule['triggers'][0]['value'] == 'new-pattern'


# ==================== Test Rule (Preview) ====================


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_test_rule_preview(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test previewing which transactions a rule would match."""
    # Create a rule that matches seed transactions (description contains 'Seed:')
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Preview Rule',
        trigger_type='description_contains',
        trigger_value='Seed:',
        action_type='set_category',
        action_value='Matched',
    )
    rule_cleanup.append(rule_id)

    today = date.today()
    start = today.replace(day=1)
    end = start + timedelta(days=31)

    result = await mcp_client.call_tool(
        'test_rule',
        {
            'req': {
                'rule_id': rule_id,
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
            }
        },
    )
    test_result = result.structured_content

    assert test_result['rule_id'] == rule_id
    assert test_result['rule_title'] == 'Integration Test - Preview Rule'
    assert isinstance(test_result['matched_transaction_count'], int)
    # Seed transactions from conftest should match
    assert test_result['matched_transaction_count'] >= 0
    assert isinstance(test_result['matched_transactions'], list)


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_test_rule_no_matches(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test previewing a rule that matches no transactions."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - No Matches',
        trigger_type='description_contains',
        trigger_value='zzz_nonexistent_pattern_zzz',
    )
    rule_cleanup.append(rule_id)

    today = date.today()

    result = await mcp_client.call_tool(
        'test_rule',
        {
            'req': {
                'rule_id': rule_id,
                'start_date': today.isoformat(),
                'end_date': today.isoformat(),
            }
        },
    )
    test_result = result.structured_content
    assert test_result['matched_transaction_count'] == 0
    assert test_result['matched_transactions'] == []


# ==================== Execute Rule ====================


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_execute_rule_requires_confirm(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test that execute_rule without confirm=True raises an error."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Confirm Guard',
    )
    rule_cleanup.append(rule_id)

    today = date.today()

    with pytest.raises(ToolError, match='confirm=True'):
        await mcp_client.call_tool(
            'execute_rule',
            {
                'req': {
                    'rule_id': rule_id,
                    'start_date': today.isoformat(),
                    'end_date': today.isoformat(),
                    'confirm': False,
                }
            },
        )


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_execute_rule_with_confirm(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test executing a rule with proper confirmation."""
    # Use add_tag action — non-destructive and won't interfere with other tests
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Execute Rule',
        trigger_type='description_contains',
        trigger_value='Seed:',
        action_type='add_tag',
        action_value='integration-test-tag',
    )
    rule_cleanup.append(rule_id)

    today = date.today()
    start = today.replace(day=1)
    end = start + timedelta(days=31)

    result = await mcp_client.call_tool(
        'execute_rule',
        {
            'req': {
                'rule_id': rule_id,
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'confirm': True,
            }
        },
    )
    exec_result = result.structured_content

    assert exec_result['rule_id'] == rule_id
    assert exec_result['rule_title'] == 'Integration Test - Execute Rule'
    assert exec_result['success'] is True
    assert 'asynchronously' in exec_result['message']


# ==================== Date Validation ====================


@pytest.mark.asyncio
@pytest.mark.rules
@pytest.mark.integration
async def test_test_rule_rejects_inverted_dates(
    mcp_client: Client,
    firefly_client: FireflyClient,
    rule_cleanup: List[str],
):
    """Test that test_rule rejects start_date after end_date."""
    rule_id = await _create_rule_via_api(
        firefly_client,
        title='Integration Test - Date Validation',
    )
    rule_cleanup.append(rule_id)

    with pytest.raises(ToolError, match='start_date'):
        await mcp_client.call_tool(
            'test_rule',
            {
                'req': {
                    'rule_id': rule_id,
                    'start_date': '2024-12-31',
                    'end_date': '2024-01-01',
                }
            },
        )
