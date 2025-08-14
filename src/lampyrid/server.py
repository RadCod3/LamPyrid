from typing import List

from fastmcp import FastMCP

from .clients.firefly import FireflyClient
from .models.lampyrid_models import (
	Account,
	CreateDepositRequest,
	CreateTransferRequest,
	CreateWithdrawalRequest,
	GetTransactionsRequest,
	ListAccountRequest,
	SearchAccountRequest,
	SearchTransactionsRequest,
	TransactionListResponse,
)

mcp = FastMCP('lampyrid')
_client = FireflyClient()


@mcp.tool()
async def list_accounts(req: ListAccountRequest) -> List[Account]:
	"""List Firefly-III accounts."""
	account_list = await _client.list_accounts(type=req.type)

	accounts: List[Account] = [
		Account.from_account_read(account_read) for account_read in account_list.data
	]

	return accounts


@mcp.tool()
async def search_accounts(req: SearchAccountRequest) -> List[Account]:
	"""Search Firefly-III accounts by name."""
	account_list = await _client.search_accounts(req)

	accounts: List[Account] = [
		Account.from_account_read(account_read) for account_read in account_list.data
	]

	return accounts


@mcp.tool()
async def create_withdrawal(req: CreateWithdrawalRequest):
	"""Create a new Firefly-III withdrawal."""
	transaction = await _client.create_withdrawal(req)
	return transaction


@mcp.tool()
async def create_deposit(req: CreateDepositRequest):
	"""Create a new Firefly-III deposit."""
	transaction = await _client.create_deposit(req)
	return transaction


@mcp.tool()
async def create_transfer(req: CreateTransferRequest):
	"""Create a new Firefly-III transfer."""
	transaction = await _client.create_transfer(req)
	return transaction


@mcp.tool()
async def get_transactions(req: GetTransactionsRequest) -> TransactionListResponse:
	"""Get past transactions with optional time range and type filtering."""
	transaction_array = await _client.get_transactions(req)

	return TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)


@mcp.tool()
async def search_transactions(req: SearchTransactionsRequest) -> TransactionListResponse:
	"""Search transactions by description or other text fields."""
	transaction_array = await _client.search_transactions(req)

	return TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)
