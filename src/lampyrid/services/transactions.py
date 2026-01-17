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
    ) -> List[Transaction]:
        """Create multiple transactions in a single operation.

        This method orchestrates the creation of multiple transactions,
        handling the business logic for bulk operations while delegating
        the individual HTTP requests to the FireflyClient.

        Args:
                req: Request containing multiple transaction details

        Returns:
                List of created transactions

        """
        created_transactions: List[Transaction] = []

        for transaction in req.transactions:
            trx_split = transaction.to_transaction_split_store()
            trx_store = TransactionStore(
                transactions=[trx_split],
                apply_rules=False,
                fire_webhooks=True,
                group_title=None,
                error_if_duplicate_hash=False,
            )
            transaction_single = await self._client.create_transaction(trx_store)
            created_transactions.append(Transaction.from_transaction_single(transaction_single))

        return created_transactions

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

        # Content filters
        if req.description_contains:
            query_parts.append(f'description_contains:"{req.description_contains}"')

        # Metadata filters
        if req.category:
            query_parts.append(f'category_is:"{req.category}"')
        if req.budget:
            query_parts.append(f'budget_is:"{req.budget}"')

        # Account filters
        if req.account_contains:
            query_parts.append(f'account_contains:"{req.account_contains}"')
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
    ) -> List[Transaction]:
        """Update multiple transactions in a single operation.

        This method orchestrates the update of multiple transactions,
        handling the business logic for bulk operations while delegating
        the individual HTTP requests to the FireflyClient.

        Args:
                req: Request containing multiple transaction updates

        Returns:
                List of updated transactions

        """
        updated_transactions: List[Transaction] = []

        for update_req in req.updates:
            try:
                updated_transaction = await self.update_transaction(update_req)
                updated_transactions.append(updated_transaction)
            except Exception as e:
                # Re-raise with transaction ID context
                raise Exception(
                    f'Failed to update transaction {update_req.transaction_id}: {e}'
                ) from e

        return updated_transactions

    async def delete_transaction(self, req: DeleteTransactionRequest) -> bool:
        """Delete a transaction.

        Args:
                req: Request containing the transaction ID to delete

        Returns:
                True if deletion was successful

        """
        result = await self._client.delete_transaction(req.id)
        return result
