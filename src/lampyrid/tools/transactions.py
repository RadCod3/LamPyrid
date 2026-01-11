"""
Transaction Management MCP Tools.

This module provides MCP tools for managing Firefly III transactions including
creating, retrieving, searching, updating, and deleting transactions.
"""

from typing import List

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
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


def create_transactions_server(client: FireflyClient) -> FastMCP:
	"""
	Create a standalone FastMCP server for transaction management tools.

	Args:
		client: The FireflyClient instance for API interactions

	Returns:
		FastMCP server instance with transaction management tools registered
	"""
	transactions_mcp = FastMCP('transactions')

	@transactions_mcp.tool(tags={'transactions', 'create'})
	async def create_withdrawal(req: CreateWithdrawalRequest) -> Transaction:
		"""Record expenses and spending. Money leaves your asset accounts to pay for goods, services, or cash withdrawals. Can be assigned to budgets for expense tracking."""
		transaction = await client.create_withdrawal(req)
		return transaction

	@transactions_mcp.tool(tags={'transactions', 'create'})
	async def create_deposit(req: CreateDepositRequest) -> Transaction:
		"""Record income and money received. Represents salary, refunds, gifts, or any money coming into your asset accounts from external sources."""
		transaction = await client.create_deposit(req)
		return transaction

	@transactions_mcp.tool(tags={'transactions', 'create'})
	async def create_transfer(req: CreateTransferRequest) -> Transaction:
		"""Move money between your own accounts. Use for transferring to savings, paying credit cards from checking, or consolidating funds."""
		transaction = await client.create_transfer(req)
		return transaction

	@transactions_mcp.tool(tags={'transactions', 'create', 'bulk'})
	async def create_bulk_transactions(req: CreateBulkTransactionsRequest) -> List[Transaction]:
		"""Efficiently create multiple transactions in one operation. Ideal for importing transaction batches, recording monthly bills, or processing CSV data."""
		transactions = await client.create_bulk_transactions(req)
		return transactions

	@transactions_mcp.tool(tags={'transactions', 'query'})
	async def get_transaction(req: GetTransactionRequest) -> Transaction:
		"""Retrieve complete transaction details. Use this to verify transaction information before updates or to examine specific transactions."""
		return await client.get_transaction(req)

	@transactions_mcp.tool(tags={'transactions', 'query'})
	async def get_transactions(req: GetTransactionsRequest) -> TransactionListResponse:
		"""Retrieve transaction history with flexible filtering and pagination. Essential for financial analysis, spending pattern review, and account activity monitoring."""
		if req.account_id is not None:
			transaction_array = await client.get_account_transactions(req)
		else:
			transaction_array = await client.get_transactions(req)

		return TransactionListResponse.from_transaction_array(
			transaction_array, current_page=req.page or 1, per_page=req.limit or 50
		)

	@transactions_mcp.tool(tags={'transactions', 'query'})
	async def search_transactions(req: SearchTransactionsRequest) -> TransactionListResponse:
		"""Search transactions with powerful filtering options. Supports free-text search, type filtering (withdrawal/deposit/transfer), amount ranges, date ranges, categories, budgets, and account matching. All filters combine with AND logic for precise results."""
		transaction_array = await client.search_transactions(req)

		return TransactionListResponse.from_transaction_array(
			transaction_array, current_page=req.page or 1, per_page=req.limit or 50
		)

	@transactions_mcp.tool(tags={'transactions', 'manage'})
	async def delete_transaction(req: DeleteTransactionRequest) -> bool:
		"""Permanently remove a transaction. Use to correct mistakes, remove duplicates, or delete test data. This action cannot be undone."""
		return await client.delete_transaction(req)

	@transactions_mcp.tool(tags={'transactions', 'manage'})
	async def update_transaction(req: UpdateTransactionRequest) -> Transaction:
		"""Modify transaction details such as amounts, descriptions, dates, accounts, or budget assignments. Useful for correcting imported data or updating incomplete information."""
		return await client.update_transaction(req)

	@transactions_mcp.tool(tags={'transactions', 'manage', 'bulk'})
	async def bulk_update_transactions(req: BulkUpdateTransactionsRequest) -> List[Transaction]:
		"""Efficiently update multiple transactions in one operation. Ideal for batch account changes, budget reassignments, or correcting imported data."""
		return await client.bulk_update_transactions(req)

	return transactions_mcp
