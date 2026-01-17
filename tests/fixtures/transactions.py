"""Test data factories for transaction-related tests."""

from datetime import date, datetime, timezone
from typing import List

from lampyrid.models.firefly_models import TransactionTypeFilter
from lampyrid.models.lampyrid_models import (
    BulkUpdateTransactionsRequest,
    CreateBulkTransactionsRequest,
    CreateDepositRequest,
    CreateTransferRequest,
    CreateWithdrawalRequest,
    DeleteTransactionRequest,
    GetTransactionRequest,
    GetTransactionsRequest,
    SearchTransactionsRequest,
    Transaction,
    UpdateTransactionRequest,
)


def make_create_withdrawal_request(
    amount: float,
    description: str,
    source_id: str,
    destination_name: str,
    budget_id: str | None = None,
    date: datetime | None = None,
) -> CreateWithdrawalRequest:
    """Create a CreateWithdrawalRequest for testing."""
    if date is None:
        date = datetime.now(timezone.utc)

    return CreateWithdrawalRequest(
        amount=amount,
        description=description,
        date=date,
        source_id=source_id,
        destination_name=destination_name,
        budget_id=budget_id,
    )


def make_create_deposit_request(
    amount: float,
    description: str,
    destination_id: str,
    source_name: str,
    date: datetime | None = None,
) -> CreateDepositRequest:
    """Create a CreateDepositRequest for testing."""
    if date is None:
        date = datetime.now(timezone.utc)

    return CreateDepositRequest(
        amount=amount,
        description=description,
        date=date,
        source_name=source_name,
        destination_id=destination_id,
    )


def make_create_transfer_request(
    amount: float,
    description: str,
    source_id: str,
    destination_id: str,
    date: datetime | None = None,
) -> CreateTransferRequest:
    """Create a CreateTransferRequest for testing."""
    if date is None:
        date = datetime.now(timezone.utc)

    return CreateTransferRequest(
        amount=amount,
        description=description,
        date=date,
        source_id=source_id,
        destination_id=destination_id,
    )


def make_create_bulk_transactions_request(
    transactions: List[Transaction],
    atomic: bool = True,
) -> CreateBulkTransactionsRequest:
    """Create a CreateBulkTransactionsRequest for testing."""
    return CreateBulkTransactionsRequest(transactions=transactions, atomic=atomic)


def make_get_transaction_request(transaction_id: str) -> GetTransactionRequest:
    """Create a GetTransactionRequest for testing."""
    return GetTransactionRequest(id=transaction_id)


def make_get_transactions_request(
    account_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: TransactionTypeFilter | None = None,
    page: int = 1,
    limit: int = 50,
) -> GetTransactionsRequest:
    """Create a GetTransactionsRequest for testing."""
    return GetTransactionsRequest(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        page=page,
        limit=limit,
    )


def make_search_transactions_request(
    query: str | None = None,
    description_contains: str | None = None,
    amount_equals: float | None = None,
    amount_more: float | None = None,
    amount_less: float | None = None,
    date_on: datetime | None = None,
    date_after: datetime | None = None,
    date_before: datetime | None = None,
    transaction_type: str | None = None,
    category: str | None = None,
    budget: str | None = None,
    account_contains: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> SearchTransactionsRequest:
    """Create a SearchTransactionsRequest for testing."""
    return SearchTransactionsRequest(
        query=query,
        description_contains=description_contains,
        amount_equals=amount_equals,
        amount_more=amount_more,
        amount_less=amount_less,
        date_on=date_on,
        date_after=date_after,
        date_before=date_before,
        type=transaction_type,  # ty:ignore[invalid-argument-type]
        category=category,
        budget=budget,
        account_contains=account_contains,
        page=page,
        limit=limit,
    )


def make_update_transaction_request(
    transaction_id: str,
    amount: float | None = None,
    description: str | None = None,
    date: datetime | None = None,
    source_id: str | None = None,
    destination_id: str | None = None,
    budget_id: str | None = None,
    category_name: str | None = None,
) -> UpdateTransactionRequest:
    """Create an UpdateTransactionRequest for testing."""
    return UpdateTransactionRequest(
        transaction_id=transaction_id,
        amount=amount,
        description=description,
        date=date,
        source_id=source_id,
        destination_id=destination_id,
        budget_id=budget_id,
        category_name=category_name,
    )


def make_bulk_update_transactions_request(
    updates: List[UpdateTransactionRequest],
) -> BulkUpdateTransactionsRequest:
    """Create a BulkUpdateTransactionsRequest for testing."""
    return BulkUpdateTransactionsRequest(updates=updates)


def make_delete_transaction_request(transaction_id: str) -> DeleteTransactionRequest:
    """Create a DeleteTransactionRequest for testing."""
    return DeleteTransactionRequest(id=transaction_id)
