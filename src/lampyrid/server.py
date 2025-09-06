from typing import List

from fastmcp import FastMCP

from .clients.firefly import FireflyClient
from .models.lampyrid_models import (
	Account,
	AvailableBudget,
	Budget,
	BudgetSpending,
	BudgetSummary,
	BulkUpdateTransactionsRequest,
	CreateBulkTransactionsRequest,
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
	UpdateTransactionRequest,
)

mcp = FastMCP('lampyrid')
_client = FireflyClient()


@mcp.tool(tags={'accounts'})
async def list_accounts(req: ListAccountRequest) -> List[Account]:
	"""Retrieve accounts from Firefly III. Use 'asset' for checking/savings accounts, 'expense' for spending accounts, 'revenue' for income sources. Essential for finding account IDs before creating transactions."""
	account_list = await _client.list_accounts(type=req.type)

	accounts: List[Account] = [
		Account.from_account_read(account_read) for account_read in account_list.data
	]

	return accounts


@mcp.tool(tags={'accounts'})
async def get_account(req: GetAccountRequest) -> Account:
	"""Retrieve detailed account information including current balance and currency. Use this to verify account details before transactions."""
	return await _client.get_account(req)


@mcp.tool(tags={'accounts'})
async def search_accounts(req: SearchAccountRequest) -> List[Account]:
	"""Find accounts by partial name matching. Useful when you know the account name but not the ID. Supports filtering by account type."""
	account_list = await _client.search_accounts(req)

	accounts: List[Account] = [
		Account.from_account_read(account_read) for account_read in account_list.data
	]

	return accounts


@mcp.tool(tags={'transactions', 'create'})
async def create_withdrawal(req: CreateWithdrawalRequest) -> Transaction:
	"""Record expenses and spending. Money leaves your asset accounts to pay for goods, services, or cash withdrawals. Can be assigned to budgets for expense tracking."""
	transaction = await _client.create_withdrawal(req)
	return transaction


@mcp.tool(tags={'transactions', 'create'})
async def create_deposit(req: CreateDepositRequest) -> Transaction:
	"""Record income and money received. Represents salary, refunds, gifts, or any money coming into your asset accounts from external sources."""
	transaction = await _client.create_deposit(req)
	return transaction


@mcp.tool(tags={'transactions', 'create'})
async def create_transfer(req: CreateTransferRequest) -> Transaction:
	"""Move money between your own accounts. Use for transferring to savings, paying credit cards from checking, or consolidating funds."""
	transaction = await _client.create_transfer(req)
	return transaction


@mcp.tool(tags={'transactions', 'create', 'bulk'})
async def create_bulk_transactions(req: CreateBulkTransactionsRequest) -> List[Transaction]:
	"""Efficiently create multiple transactions in one operation. Ideal for importing transaction batches, recording monthly bills, or processing CSV data."""
	transactions = await _client.create_bulk_transactions(req)
	return transactions


@mcp.tool(tags={'transactions', 'query'})
async def get_transaction(req: GetTransactionRequest) -> Transaction:
	"""Retrieve complete transaction details. Use this to verify transaction information before updates or to examine specific transactions."""
	return await _client.get_transaction(req)


@mcp.tool(tags={'transactions', 'query'})
async def get_transactions(req: GetTransactionsRequest) -> TransactionListResponse:
	"""Retrieve transaction history with flexible filtering and pagination. Essential for financial analysis, spending pattern review, and account activity monitoring."""
	transaction_array = await _client.get_transactions(req)

	return TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)


@mcp.tool(tags={'transactions', 'query'})
async def search_transactions(req: SearchTransactionsRequest) -> TransactionListResponse:
	"""Find transactions by searching text content. Perfect for locating specific purchases, payments, or merchants by description."""
	transaction_array = await _client.search_transactions(req)

	return TransactionListResponse.from_transaction_array(
		transaction_array, current_page=req.page or 1, per_page=req.limit or 50
	)


@mcp.tool(tags={'transactions', 'manage'})
async def delete_transaction(req: DeleteTransactionRequest) -> bool:
	"""Permanently remove a transaction. Use to correct mistakes, remove duplicates, or delete test data. This action cannot be undone."""
	return await _client.delete_transaction(req)


@mcp.tool(tags={'transactions', 'manage'})
async def update_transaction(req: UpdateTransactionRequest) -> Transaction:
	"""Modify transaction details such as amounts, descriptions, dates, accounts, or budget assignments. Useful for correcting imported data or updating incomplete information."""
	return await _client.update_transaction(req)


@mcp.tool(tags={'transactions', 'manage', 'bulk'})
async def bulk_update_transactions(req: BulkUpdateTransactionsRequest) -> List[Transaction]:
	"""Efficiently update multiple transactions in one operation. Ideal for batch account changes, budget reassignments, or correcting imported data."""
	return await _client.bulk_update_transactions(req)


@mcp.tool(tags={'budgets'})
async def list_budgets(req: ListBudgetsRequest) -> List[Budget]:
	"""Retrieve your budgets for expense tracking and financial planning. Filter by active status to see current or all budgets."""
	budget_array = await _client.list_budgets(req)

	budgets: List[Budget] = [
		Budget.from_budget_read(budget_read) for budget_read in budget_array.data
	]

	return budgets


@mcp.tool(tags={'budgets'})
async def get_budget(req: GetBudgetRequest) -> Budget:
	"""Retrieve detailed budget information including name, status, and notes. Use this to verify budget details before assigning transactions."""
	return await _client.get_budget(req)


@mcp.tool(tags={'budgets', 'analysis'})
async def get_budget_spending(req: GetBudgetSpendingRequest) -> BudgetSpending:
	"""Analyze spending against a budget including amount spent, remaining budget, and percentage used. Essential for budget monitoring and overspending alerts."""
	return await _client.get_budget_spending(req)


@mcp.tool(tags={'budgets', 'analysis'})
async def get_budget_summary(req: GetBudgetSummaryRequest) -> BudgetSummary:
	"""Comprehensive overview of all budget performance with totals and spending analysis. Perfect for monthly reviews and financial dashboards."""
	return await _client.get_budget_summary(req)


@mcp.tool(tags={'budgets', 'analysis'})
async def get_available_budget(req: GetAvailableBudgetRequest) -> AvailableBudget:
	"""Check unallocated budget available for new budgets or unexpected expenses. Shows money set aside but not assigned to specific budgets."""
	return await _client.get_available_budget(req)
