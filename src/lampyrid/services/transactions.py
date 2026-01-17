"""Transaction Service for LamPyrid.

This service handles transaction-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

from typing import List

from ..clients.firefly import FireflyClient
from ..models.firefly_models import (
    TransactionSplitStore,
    TransactionSplitUpdate,
    TransactionStore,
    TransactionTypeProperty,
    TransactionUpdate,
)
from ..models.lampyrid_models import (
    BulkCreateResult,
    BulkOperationError,
    BulkUpdateResult,
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
    TransactionListResponse,
    UpdateTransactionRequest,
)


class TransactionService:
    """Service for managing Firefly III transactions.

    This service provides a high-level interface for transaction operations,
    handling bulk operations, model conversion, and business logic while
    delegating HTTP operations to the FireflyClient.
    """

    def __init__(self, client: FireflyClient) -> None:
        """Initialize the transaction service with a FireflyClient instance."""
        self._client = client

    async def create_withdrawal(self, req: CreateWithdrawalRequest) -> Transaction:
        """Create a withdrawal transaction.

        Args:
                req: Withdrawal transaction details

        Returns:
                Created transaction details

        """
        trx = TransactionSplitStore(
            amount=str(req.amount),
            description=req.description,
            type=TransactionTypeProperty.withdrawal,
            date=req.date,
            source_id=req.source_id,
            destination_name=req.destination_name,
            budget_id=req.budget_id,
            budget_name=req.budget_name,
        )
        trx_store = TransactionStore(
            transactions=[trx],
            apply_rules=False,
            fire_webhooks=True,
            group_title=None,
            error_if_duplicate_hash=False,
        )
        transaction_single = await self._client.create_transaction(trx_store)
        return Transaction.from_transaction_single(transaction_single)

    async def create_deposit(self, req: CreateDepositRequest) -> Transaction:
        """Create a deposit transaction.

        Args:
                req: Deposit transaction details

        Returns:
                Created transaction details

        """
        trx = TransactionSplitStore(
            amount=str(req.amount),
            description=req.description,
            type=TransactionTypeProperty.deposit,
            date=req.date,
            source_name=req.source_name,
            destination_id=req.destination_id,
        )
        trx_store = TransactionStore(
            transactions=[trx],
            apply_rules=False,
            fire_webhooks=True,
            group_title=None,
            error_if_duplicate_hash=False,
        )
        transaction_single = await self._client.create_transaction(trx_store)
        return Transaction.from_transaction_single(transaction_single)

    async def create_transfer(self, req: CreateTransferRequest) -> Transaction:
        """Create a transfer transaction.

        Args:
                req: Transfer transaction details

        Returns:
                Created transaction details

        """
        trx = TransactionSplitStore(
            amount=str(req.amount),
            description=req.description,
            type=TransactionTypeProperty.transfer,
            date=req.date,
            source_id=req.source_id,
            destination_id=req.destination_id,
        )
        trx_store = TransactionStore(
            transactions=[trx],
            apply_rules=False,
            fire_webhooks=True,
            group_title=None,
            error_if_duplicate_hash=False,
        )
        transaction_single = await self._client.create_transaction(trx_store)
        return Transaction.from_transaction_single(transaction_single)

    async def create_bulk_transactions(
        self, req: CreateBulkTransactionsRequest
    ) -> BulkCreateResult:
        """Create multiple transactions in a single operation.

        Supports two modes:
        - atomic=True (default): Rolls back all created transactions if any fails
        - atomic=False: Continues on error and returns partial results

        Args:
            req: Request containing transaction details and atomic flag

        Returns:
            BulkCreateResult with successful/failed transactions

        Raises:
            Exception: In atomic mode if any creation fails (after rollback)
            Exception: In non-atomic mode if ALL creations fail

        """
        if req.atomic:
            return await self._create_bulk_atomic(req.transactions)
        else:
            return await self._create_bulk_non_atomic(req.transactions)

    async def _create_bulk_atomic(self, transactions: List[Transaction]) -> BulkCreateResult:
        """Create transactions atomically - rollback all on any failure."""
        created: List[Transaction] = []
        created_ids: List[str] = []

        try:
            for idx, transaction in enumerate(transactions):
                trx_split = transaction.to_transaction_split_store()
                trx_store = TransactionStore(
                    transactions=[trx_split],
                    apply_rules=False,
                    fire_webhooks=True,
                    group_title=None,
                    error_if_duplicate_hash=False,
                )
                transaction_single = await self._client.create_transaction(trx_store)
                result = Transaction.from_transaction_single(transaction_single)
                created.append(result)
                if result.id:
                    created_ids.append(result.id)
        except Exception as e:
            # Rollback: delete all created transactions
            rollback_failures: List[str] = []
            for txn_id in created_ids:
                try:
                    await self._client.delete_transaction(txn_id)
                except Exception as rollback_error:
                    rollback_failures.append(f'{txn_id}: {rollback_error}')

            error_msg = (
                f'Bulk creation failed at index {len(created_ids)}, '
                f'rolled back {len(created_ids)} transactions: {e}'
            )
            if rollback_failures:
                error_msg += f' Rollback failures: {rollback_failures}'
            raise Exception(error_msg) from e

        return BulkCreateResult(
            successful=created,
            failed=[],
            total_requested=len(transactions),
            total_succeeded=len(created),
            total_failed=0,
        )

    async def _create_bulk_non_atomic(self, transactions: List[Transaction]) -> BulkCreateResult:
        """Create transactions non-atomically - continue on error."""
        successful: List[Transaction] = []
        failed: List[BulkOperationError] = []

        for idx, transaction in enumerate(transactions):
            try:
                trx_split = transaction.to_transaction_split_store()
                trx_store = TransactionStore(
                    transactions=[trx_split],
                    apply_rules=False,
                    fire_webhooks=True,
                    group_title=None,
                    error_if_duplicate_hash=False,
                )
                transaction_single = await self._client.create_transaction(trx_store)
                successful.append(Transaction.from_transaction_single(transaction_single))
            except Exception as e:
                failed.append(BulkOperationError(index=idx, error=str(e)))

        if len(failed) == len(transactions):
            raise Exception(f'All {len(transactions)} transactions failed to create')

        return BulkCreateResult(
            successful=successful,
            failed=failed,
            total_requested=len(transactions),
            total_succeeded=len(successful),
            total_failed=len(failed),
        )

    async def get_transaction(self, req: GetTransactionRequest) -> Transaction:
        """Get detailed information for a single transaction.

        Args:
                req: Request containing the transaction ID

        Returns:
                Transaction details

        """
        transaction_single = await self._client.get_transaction(req.id)
        return Transaction.from_transaction_single(transaction_single)

    async def get_transactions(self, req: GetTransactionsRequest) -> TransactionListResponse:
        """Get transactions with optional filtering and pagination.

        Args:
                req: Request containing filter criteria and pagination parameters

        Returns:
                Paginated list of transactions

        """
        if req.account_id is not None:
            transaction_array = await self._client.get_account_transactions(
                account_id=req.account_id,
                page=req.page or 1,
                limit=req.limit or 50,
                start_date=req.start_date,
                end_date=req.end_date,
                transaction_type=req.transaction_type.value if req.transaction_type else None,
            )
        else:
            transaction_array = await self._client.get_transactions(
                page=req.page or 1,
                limit=req.limit or 50,
                start_date=req.start_date,
                end_date=req.end_date,
                transaction_type=req.transaction_type.value if req.transaction_type else None,
            )

        return TransactionListResponse.from_transaction_array(
            transaction_array, current_page=req.page or 1, per_page=req.limit or 50
        )

    async def search_transactions(self, req: SearchTransactionsRequest) -> TransactionListResponse:
        """Search transactions with advanced filtering.

        Args:
                req: Request containing search criteria and filters

        Returns:
                Paginated list of matching transactions

        """
        # Build query string from structured fields
        query_parts = []

        # Add raw query if provided
        if req.query:
            query_parts.append(req.query)

        # Transaction type and amount filters
        if req.type:
            query_parts.append(f'type:{req.type}')
        if req.amount_equals is not None:
            query_parts.append(f'amount:{req.amount_equals}')
        if req.amount_more is not None:
            query_parts.append(f'more:{req.amount_more}')
        if req.amount_less is not None:
            query_parts.append(f'less:{req.amount_less}')

        # Date filters
        if req.date_on:
            query_parts.append(f'date_on:{req.date_on}')
        if req.date_after:
            query_parts.append(f'date_after:{req.date_after}')
        if req.date_before:
            query_parts.append(f'date_before:{req.date_before}')

        # Content filters - sanitize user-provided values to escape special characters
        if req.description_contains:
            sanitized = FireflyClient._sanitize_value(req.description_contains)
            query_parts.append(f'description_contains:{sanitized}')

        # Metadata filters - sanitize user-provided values to escape special characters
        if req.category:
            sanitized = FireflyClient._sanitize_value(req.category)
            query_parts.append(f'category_is:{sanitized}')
        if req.budget:
            sanitized = FireflyClient._sanitize_value(req.budget)
            query_parts.append(f'budget_is:{sanitized}')

        # Account filters - sanitize user-provided values to escape special characters
        if req.account_contains:
            sanitized = FireflyClient._sanitize_value(req.account_contains)
            query_parts.append(f'account_contains:{sanitized}')
        if req.account_id is not None:
            query_parts.append(f'account_id:{req.account_id}')

        # Combine all query parts with spaces (AND logic)
        final_query = ' '.join(query_parts)

        transaction_array = await self._client.search_transactions(
            query=final_query, page=req.page or 1, limit=req.limit or 50
        )

        return TransactionListResponse.from_transaction_array(
            transaction_array, current_page=req.page or 1, per_page=req.limit or 50
        )

    async def update_transaction(self, req: UpdateTransactionRequest) -> Transaction:
        """Update an existing transaction.

        Args:
                req: Request containing updated transaction details

        Returns:
                Updated transaction details

        """
        # Build the update payload with only provided fields using explicit parameters
        update_kwargs = {}

        if req.amount is not None:
            update_kwargs['amount'] = str(req.amount)
        if req.description is not None:
            update_kwargs['description'] = req.description
        if req.date is not None:
            update_kwargs['date'] = req.date
        if req.source_id is not None:
            update_kwargs['source_id'] = req.source_id
        if req.destination_id is not None:
            update_kwargs['destination_id'] = req.destination_id
        if req.budget_id is not None:
            update_kwargs['budget_id'] = req.budget_id
        if req.category_name is not None:
            update_kwargs['category_name'] = req.category_name

        trx_split_update = TransactionSplitUpdate(**update_kwargs)

        transaction_update = TransactionUpdate(
            apply_rules=False, fire_webhooks=True, group_title=None, transactions=[trx_split_update]
        )

        transaction_single = await self._client.update_transaction(
            req.transaction_id, transaction_update
        )
        return Transaction.from_transaction_single(transaction_single)

    async def bulk_update_transactions(
        self, req: BulkUpdateTransactionsRequest
    ) -> BulkUpdateResult:
        """Update multiple transactions in a single operation.

        Continues processing on errors and returns partial results.

        Args:
            req: Request containing multiple transaction updates

        Returns:
            BulkUpdateResult with successful/failed updates

        Raises:
            Exception: If ALL updates fail

        """
        successful: List[Transaction] = []
        failed: List[BulkOperationError] = []

        for idx, update_req in enumerate(req.updates):
            try:
                updated_transaction = await self.update_transaction(update_req)
                successful.append(updated_transaction)
            except Exception as e:
                failed.append(
                    BulkOperationError(
                        index=idx,
                        transaction_id=update_req.transaction_id,
                        error=str(e),
                    )
                )

        if len(failed) == len(req.updates):
            raise Exception(f'All {len(req.updates)} transaction updates failed')

        return BulkUpdateResult(
            successful=successful,
            failed=failed,
            total_requested=len(req.updates),
            total_succeeded=len(successful),
            total_failed=len(failed),
        )

    async def delete_transaction(self, req: DeleteTransactionRequest) -> bool:
        """Delete a transaction.

        Args:
                req: Request containing the transaction ID to delete

        Returns:
                True if deletion was successful

        """
        result = await self._client.delete_transaction(req.id)
        return result
