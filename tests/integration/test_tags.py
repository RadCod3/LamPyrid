"""Integration tests for tag management tools.

These exercise the tag tools against a real Firefly III instance and verify that
tags submitted on transactions are auto-created, listable, and retrievable by
name.
"""

from datetime import datetime, timezone
from typing import List

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from lampyrid.models.lampyrid_models import Account, Tag, Transaction


@pytest.mark.asyncio
@pytest.mark.tags
@pytest.mark.integration
async def test_tags_auto_created_and_listed(
    mcp_client: Client,
    test_asset_account: Account,
    test_expense_account: str,
    transaction_cleanup: List[str],
):
    """Unknown tags submitted on a withdrawal are auto-created and listed."""
    tags = ['integration-tag-alpha', 'integration-tag-beta']

    result = await mcp_client.call_tool(
        'create_withdrawal',
        {
            'req': {
                'amount': 8.25,
                'description': 'Withdrawal with tags',
                'source_id': test_asset_account.id,
                'destination_name': test_expense_account,
                'tags': tags,
                'date': datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    transaction = Transaction.model_validate(result.structured_content)
    assert transaction.id is not None
    transaction_cleanup.append(transaction.id)
    assert set(transaction.tags or []) == set(tags)

    listed = await mcp_client.call_tool('list_tags', {})
    tag_names = {Tag.model_validate(t).tag for t in listed.structured_content['result']}
    assert set(tags).issubset(tag_names)


@pytest.mark.asyncio
@pytest.mark.tags
@pytest.mark.integration
async def test_get_tag_by_name(
    mcp_client: Client,
    test_asset_account: Account,
    test_expense_account: str,
    transaction_cleanup: List[str],
):
    """A tag can be retrieved by its name and by its numeric ID."""
    tag_name = 'integration-tag-getbyname'

    result = await mcp_client.call_tool(
        'create_withdrawal',
        {
            'req': {
                'amount': 5.0,
                'description': 'Withdrawal for get_tag',
                'source_id': test_asset_account.id,
                'destination_name': test_expense_account,
                'tags': [tag_name],
                'date': datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    transaction = Transaction.model_validate(result.structured_content)
    assert transaction.id is not None
    transaction_cleanup.append(transaction.id)

    # Lookup by name.
    by_name = await mcp_client.call_tool('get_tag', {'req': {'tag': tag_name}})
    tag = Tag.model_validate(by_name.structured_content)
    assert tag.tag == tag_name
    assert tag.id is not None

    # Lookup by the numeric ID returns the same tag.
    by_id = await mcp_client.call_tool('get_tag', {'req': {'tag': tag.id}})
    same_tag = Tag.model_validate(by_id.structured_content)
    assert same_tag.id == tag.id
    assert same_tag.tag == tag_name


@pytest.mark.asyncio
@pytest.mark.tags
@pytest.mark.integration
async def test_get_tag_unknown_raises(mcp_client: Client):
    """Requesting a non-existent tag raises an error."""
    with pytest.raises(ToolError):
        await mcp_client.call_tool('get_tag', {'req': {'tag': 'definitely-not-a-real-tag-xyz-123'}})
