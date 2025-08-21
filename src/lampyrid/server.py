from typing import List

from fastmcp import FastMCP

from .clients.firefly import FireflyClient
from .models.lampyrid_models import (
	Account,
	AvailableBudget,
	Budget,
	BudgetSpending,
	BudgetSummary,
	CreateDepositRequest,
	CreateTransferRequest,
	CreateWithdrawalRequest,
	DeleteTransactionRequest,
	GetAccountRequest,
	GetAvailableBudgetRequest,
	GetBudgetRequest,
	GetBudgetSpendingRequest,
	GetBudgetSummaryRequest,
	GetTransactionRequest,
	GetTransactionsRequest,
	ListAccountRequest,
	ListBudgetsRequest,
	SearchAccountRequest,
	SearchTransactionsRequest,
	Transaction,
	TransactionListResponse,
	UpdateTransactionBudgetRequest,
)

mcp = FastMCP('lampyrid')
_client = FireflyClient()


@mcp.tool(tags={'accounts'})
async def list_accounts(req: ListAccountRequest) -> List[Account]:
	"""List Firefly-III accounts."""
	account_list = await _client.list_accounts(type=req.type)

	accounts: List[Account] = [
		Account.from_account_read(account_read) for account_read in account_list.data
	]

	return accounts


@mcp.tool(tags={'accounts'})
async def get_account(req: GetAccountRequest) -> Account:
	"""Get a single Firefly-III account by ID."""
	return await _client.get_account(req)


@mcp.tool(tags={'accounts'})
async def search_accounts(req: SearchAccountRequest) -> List[Account]:
	"""Search Firefly-III accounts by name."""
	account_list = await _client.search_accounts(req)

	accounts: List[Account] = [
		Account.from_account_read(account_read) for account_read in account_list.data
	]

	return accounts


@mcp.tool(tags={'transactions', 'create'})
async def create_withdrawal(req: CreateWithdrawalRequest) -> Transaction:
	"""Create a new Firefly-III withdrawal."""
	transaction = await _client.create_withdrawal(req)
	return transaction


@mcp.tool(tags={'transactions', 'create'})
async def create_deposit(req: CreateDepositRequest) -> Transaction:
	"""Create a new Firefly-III deposit."""
	transaction = await _client.create_deposit(req)
	return transaction


@mcp.tool(tags={'transactions', 'create'})
async def create_transfer(req: CreateTransferRequest) -> Transaction:
	"""Create a new Firefly-III transfer."""
	transaction = await _client.create_transfer(req)
	return transaction


@mcp.tool(tags={'transactions', 'query'})
async def get_transaction(req: GetTransactionRequest) -> Transaction:
	"""Get a single transaction by ID."""
	return await _client.get_transaction(req)


@mcp.tool(tags={'transactions', 'query'})
async def get_transactions(req: GetTransactionsRequest) -> TransactionListResponse:
	"""Get past transactions with optional time range and type filtering."""
	transaction_array = await _client.get_transactions(req)

	return TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)


@mcp.tool(tags={'transactions', 'query'})
async def search_transactions(req: SearchTransactionsRequest) -> TransactionListResponse:
	"""Search transactions by description or other text fields."""
	transaction_array = await _client.search_transactions(req)

	return TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)


@mcp.tool(tags={'transactions', 'manage'})
async def delete_transaction(req: DeleteTransactionRequest) -> bool:
	"""Delete a transaction by ID."""
	return await _client.delete_transaction(req)


@mcp.tool(tags={'budgets'})
async def list_budgets(req: ListBudgetsRequest) -> List[Budget]:
	"""List Firefly-III budgets."""
	budget_array = await _client.list_budgets(req)

	budgets: List[Budget] = [
		Budget.from_budget_read(budget_read) for budget_read in budget_array.data
	]

	return budgets


@mcp.tool(tags={'transactions', 'budgets', 'manage'})
async def update_transaction_budget(req: UpdateTransactionBudgetRequest) -> Transaction:
	"""Update a transaction's budget allocation."""
	return await _client.update_transaction_budget(req)


@mcp.tool(tags={'budgets'})
async def get_budget(req: GetBudgetRequest) -> Budget:
	"""Get a single budget by ID."""
	return await _client.get_budget(req)


@mcp.tool(tags={'budgets', 'analysis'})
async def get_budget_spending(req: GetBudgetSpendingRequest) -> BudgetSpending:
	"""Get budget spending data for a specific budget and period."""
	return await _client.get_budget_spending(req)


@mcp.tool(tags={'budgets', 'analysis'})
async def get_budget_summary(req: GetBudgetSummaryRequest) -> BudgetSummary:
	"""Get summary of all budgets with spending information."""
	return await _client.get_budget_summary(req)


@mcp.tool(tags={'budgets', 'analysis'})
async def get_available_budget(req: GetAvailableBudgetRequest) -> AvailableBudget:
	"""Get available budget for a period."""
	return await _client.get_available_budget(req)
