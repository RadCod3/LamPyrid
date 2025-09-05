from datetime import date, datetime, timezone

from lampyrid.models.lampyrid_models import (
	Account,
	Budget,
	Transaction,
	TransactionType,
	ListAccountRequest,
	ListBudgetsRequest,
	SearchAccountRequest,
	CreateWithdrawalRequest,
	CreateDepositRequest,
	CreateTransferRequest,
	GetTransactionsRequest,
	SearchTransactionsRequest,
	TransactionListResponse,
	utc_now,
)
from lampyrid.models.firefly_models import AccountTypeFilter, TransactionTypeFilter


class TestAccount:
	"""Test Account model"""

	def test_from_account_read(self, sample_account_read):
		"""Test creating Account from AccountRead"""
		account = Account.from_account_read(sample_account_read)

		assert account.id == '123'
		assert account.name == 'Test Account'
		assert account.currency_code == 'USD'
		assert account.current_balance == 1000.0

	def test_from_account_read_no_balance(self, sample_account_read):
		"""Test creating Account from AccountRead with no balance"""
		sample_account_read.attributes.current_balance = None
		account = Account.from_account_read(sample_account_read)

		assert account.current_balance is None

	def test_account_validation(self):
		"""Test Account model validation"""
		account = Account(
			id='test-id', name='Test Account', currency_code='EUR', current_balance=500.50
		)

		assert account.id == 'test-id'
		assert account.name == 'Test Account'
		assert account.currency_code == 'EUR'
		assert account.current_balance == 500.50


class TestTransaction:
	"""Test Transaction model"""

	def test_transaction_creation(self):
		"""Test creating a Transaction"""
		now = datetime.now(timezone.utc)
		transaction = Transaction(
			amount=100.0,
			description='Test transaction',
			type=TransactionType.withdrawal,
			date=now,
			source_id='1',
			destination_id='2',
		)

		assert transaction.amount == 100.0
		assert transaction.description == 'Test transaction'
		assert transaction.type == TransactionType.withdrawal
		assert transaction.date == now
		assert transaction.source_id == '1'
		assert transaction.destination_id == '2'

	def test_from_transaction_single(self, sample_transaction_single):
		"""Test creating Transaction from TransactionSingle"""
		transaction = Transaction.from_transaction_single(sample_transaction_single)

		assert transaction.amount == 100.0
		assert transaction.description == 'Test transaction'
		assert transaction.type == TransactionType.withdrawal
		assert transaction.source_id == '1'
		assert transaction.destination_id == '2'

	def test_to_transaction_split_store(self):
		"""Test converting Transaction to TransactionSplitStore"""
		transaction = Transaction(
			amount=50.0,
			description='Transfer test',
			type=TransactionType.transfer,
			source_id='account1',
			destination_id='account2',
		)

		split_store = transaction.to_transaction_split_store()

		assert split_store.amount == '50.0'
		assert split_store.description == 'Transfer test'
		assert split_store.type.value == 'transfer'


class TestRequestModels:
	"""Test request models"""

	def test_list_account_request(self):
		"""Test ListAccountRequest"""
		request = ListAccountRequest(type=AccountTypeFilter.asset)
		assert request.type == AccountTypeFilter.asset

	def test_search_account_request(self):
		"""Test SearchAccountRequest"""
		request = SearchAccountRequest(query='checking', type=AccountTypeFilter.asset)
		assert request.query == 'checking'
		assert request.type == AccountTypeFilter.asset

	def test_search_account_request_default_type(self):
		"""Test SearchAccountRequest with default type"""
		request = SearchAccountRequest(query='savings')
		assert request.query == 'savings'
		assert request.type == AccountTypeFilter.all

	def test_create_withdrawal_request(self):
		"""Test CreateWithdrawalRequest"""
		request = CreateWithdrawalRequest(
			amount=100.0,
			description='ATM withdrawal',
			source_id='account1',
			destination_name='Cash',
		)

		assert request.amount == 100.0
		assert request.description == 'ATM withdrawal'
		assert request.source_id == 'account1'
		assert request.destination_name == 'Cash'

	def test_create_withdrawal_request_no_destination(self):
		"""Test CreateWithdrawalRequest without destination name"""
		request = CreateWithdrawalRequest(
			amount=50.0, description='Cash withdrawal', source_id='account1'
		)

		assert request.destination_name is None

	def test_create_deposit_request(self):
		"""Test CreateDepositRequest"""
		request = CreateDepositRequest(
			amount=200.0,
			description='Salary deposit',
			source_name='Employer',
			destination_id='account1',
		)

		assert request.amount == 200.0
		assert request.description == 'Salary deposit'
		assert request.source_name == 'Employer'
		assert request.destination_id == 'account1'

	def test_create_transfer_request(self):
		"""Test CreateTransferRequest"""
		request = CreateTransferRequest(
			amount=150.0,
			description='Account transfer',
			source_id='account1',
			destination_id='account2',
		)

		assert request.amount == 150.0
		assert request.description == 'Account transfer'
		assert request.source_id == 'account1'
		assert request.destination_id == 'account2'


class TestGetTransactionsModels:
	"""Test transaction listing models"""

	def test_get_transactions_request(self):
		"""Test GetTransactionsRequest validation"""
		# Test with all optional parameters
		request = GetTransactionsRequest(
			start_date=date(2023, 1, 1),
			end_date=date(2023, 12, 31),
			transaction_type=TransactionTypeFilter.withdrawal,
			page=2,
			limit=25,
		)

		assert request.start_date == date(2023, 1, 1)
		assert request.end_date == date(2023, 12, 31)
		assert request.transaction_type == TransactionTypeFilter.withdrawal
		assert request.page == 2
		assert request.limit == 25

	def test_get_transactions_request_defaults(self):
		"""Test GetTransactionsRequest with default values"""
		request = GetTransactionsRequest()

		assert request.start_date is None
		assert request.end_date is None
		assert request.transaction_type is None
		assert request.page == 1
		assert request.limit == 50

	def test_transaction_summary(self):
		"""Test Transaction model with summary fields"""
		summary = Transaction(
			id='123',
			description='Test transaction',
			amount=100.0,
			date=datetime(2023, 1, 1, 12, 0, 0),
			type=TransactionType.withdrawal,
			source_name='Source Account',
			destination_name='Destination Account',
			currency_code='USD',
		)

		assert summary.id == '123'
		assert summary.description == 'Test transaction'
		assert summary.amount == 100.0
		assert summary.type == TransactionType.withdrawal
		assert summary.source_name == 'Source Account'
		assert summary.destination_name == 'Destination Account'
		assert summary.currency_code == 'USD'

	def test_transaction_list_response(self):
		"""Test TransactionListResponse model"""
		transactions = [
			Transaction(
				id='123',
				description='Test',
				amount=100.0,
				date=datetime(2023, 1, 1, 12, 0, 0),
				type=TransactionType.withdrawal,
			)
		]

		response = TransactionListResponse(
			transactions=transactions, total_count=1, current_page=1, per_page=50
		)

		assert len(response.transactions) == 1
		assert response.total_count == 1
		assert response.current_page == 1
		assert response.per_page == 50

	def test_search_transactions_request(self):
		"""Test SearchTransactionsRequest validation"""
		request = SearchTransactionsRequest(
			query='groceries',
			page=2,
			limit=25,
		)

		assert request.query == 'groceries'
		assert request.page == 2
		assert request.limit == 25

	def test_search_transactions_request_defaults(self):
		"""Test SearchTransactionsRequest with default values"""
		request = SearchTransactionsRequest(query='test')

		assert request.query == 'test'
		assert request.page == 1
		assert request.limit == 50


class TestBudget:
	"""Test Budget model"""

	def test_from_budget_read(self, sample_budget_read):
		"""Test creating Budget from BudgetRead"""
		budget = Budget.from_budget_read(sample_budget_read)

		assert budget.id == '789'
		assert budget.name == 'Groceries'
		assert budget.active is True
		assert budget.notes == 'Monthly grocery budget'
		assert budget.order == 1

	def test_budget_creation(self):
		"""Test Budget model creation"""
		budget = Budget(
			id='123',
			name='Entertainment',
			active=False,
			notes='Monthly entertainment budget',
			order=2,
		)

		assert budget.id == '123'
		assert budget.name == 'Entertainment'
		assert budget.active is False
		assert budget.notes == 'Monthly entertainment budget'
		assert budget.order == 2


class TestBudgetRequests:
	"""Test budget-related request models"""

	def test_list_budgets_request(self):
		"""Test ListBudgetsRequest"""
		request = ListBudgetsRequest(active=True)
		assert request.active is True

	def test_list_budgets_request_defaults(self):
		"""Test ListBudgetsRequest with default values"""
		request = ListBudgetsRequest()
		assert request.active is None


class TestTransactionWithBudget:
	"""Test Transaction model with budget fields"""

	def test_transaction_with_budget(self):
		"""Test Transaction model with budget information"""
		transaction = Transaction(
			id='123',
			description='Grocery shopping',
			amount=50.0,
			date=datetime(2023, 1, 1, 12, 0, 0),
			type=TransactionType.withdrawal,
			source_id='1',
			destination_name='Supermarket',
			budget_id='789',
			budget_name='Groceries',
		)

		assert transaction.id == '123'
		assert transaction.description == 'Grocery shopping'
		assert transaction.amount == 50.0
		assert transaction.type == TransactionType.withdrawal
		assert transaction.budget_id == '789'
		assert transaction.budget_name == 'Groceries'

	def test_create_withdrawal_request_with_budget(self):
		"""Test CreateWithdrawalRequest with budget fields"""
		request = CreateWithdrawalRequest(
			amount=100.0,
			description='Grocery shopping',
			source_id='1',
			destination_name='Supermarket',
			budget_id='789',
			budget_name='Groceries',
		)

		assert request.amount == 100.0
		assert request.description == 'Grocery shopping'
		assert request.source_id == '1'
		assert request.destination_name == 'Supermarket'
		assert request.budget_id == '789'
		assert request.budget_name == 'Groceries'


class TestUtilityFunctions:
	"""Test utility functions"""

	def test_utc_now(self):
		"""Test utc_now function"""
		now = utc_now()
		assert now.tzinfo == timezone.utc
		assert isinstance(now, datetime)
