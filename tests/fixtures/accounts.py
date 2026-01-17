"""Test data factories for account-related tests."""

from lampyrid.models.firefly_models import AccountTypeFilter
from lampyrid.models.lampyrid_models import (
    GetAccountRequest,
    ListAccountRequest,
    SearchAccountRequest,
)


def make_list_account_request(type: AccountTypeFilter) -> ListAccountRequest:
    """Create a ListAccountRequest for testing."""
    return ListAccountRequest(type=type)


def make_search_account_request(
    query: str, type: AccountTypeFilter | None = None
) -> SearchAccountRequest:
    """Create a SearchAccountRequest for testing."""
    if type is None:
        return SearchAccountRequest(query=query)
    return SearchAccountRequest(query=query, type=type)


def make_get_account_request(account_id: str) -> GetAccountRequest:
    """Create a GetAccountRequest for testing."""
    return GetAccountRequest(id=account_id)
