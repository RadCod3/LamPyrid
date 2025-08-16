import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from lampyrid.clients.firefly import FireflyClient
from lampyrid.models.firefly_models import (
	AccountArray,
	AccountRead,
	AccountSingle,
	Account as FireflyAccount,
	Budget as FireflyBudget,
	BudgetArray,
	BudgetRead,
	ShortAccountTypeProperty,
	TransactionArray,
	TransactionSingle,
	TransactionRead,
	Transaction as FireflyTransaction,
	TransactionSplit,
	TransactionTypeProperty,
	ObjectLink,
	Meta,
	Pagination,
	PageLink,
)
from lampyrid.models.lampyrid_models import Account, Budget


@pytest.fixture
def mock_firefly_client():
	"""Mock FireflyClient for testing"""
	client = AsyncMock(spec=FireflyClient)
	return client


@pytest.fixture
def sample_firefly_account() -> FireflyAccount:
	"""Sample Firefly Account attributes for testing"""
	return FireflyAccount(
		name='Test Account',
		type=ShortAccountTypeProperty.asset,
		currency_code='USD',
		current_balance='1000.00',
	)


@pytest.fixture
def sample_account_read(sample_firefly_account: FireflyAccount) -> AccountRead:
	"""Sample AccountRead object for testing"""
	return AccountRead(id='123', type='accounts', attributes=sample_firefly_account)


@pytest.fixture
def sample_account_array(sample_account_read: AccountRead) -> AccountArray:
	"""Sample AccountArray for testing"""
	return AccountArray(
		data=[sample_account_read],
		meta=Meta(
			pagination=Pagination(total=1, count=1, per_page=10, current_page=1, total_pages=1)
		),
	)


@pytest.fixture
def sample_account_single(sample_account_read: AccountRead) -> AccountSingle:
	"""Sample AccountSingle for testing"""
	return AccountSingle(data=sample_account_read)


@pytest.fixture
def sample_account(sample_account_read: AccountRead) -> Account:
	"""Sample Account model for testing"""
	return Account.from_account_read(sample_account_read)


@pytest.fixture
def sample_transaction_split() -> TransactionSplit:
	"""Sample transaction split for testing"""
	return TransactionSplit(
		user='1',
		transaction_journal_id='1',
		order=0,
		currency_id='1',
		currency_code='USD',
		currency_symbol='$',
		currency_name='US Dollar',
		currency_decimal_places=2,
		foreign_currency_id=None,
		foreign_currency_code=None,
		foreign_currency_symbol=None,
		foreign_currency_decimal_places=None,
		foreign_amount=None,
		amount='100.00',
		description='Test transaction',
		source_id='1',
		source_name='Test Source',
		source_iban=None,
		destination_id='2',
		destination_name='Test Destination',
		destination_iban=None,
		budget_id=None,
		budget_name=None,
		category_id=None,
		category_name=None,
		bill_id=None,
		bill_name=None,
		reconciled=False,
		notes=None,
		tags=[],
		internal_reference=None,
		external_id=None,
		external_url=None,
		original_source=None,
		recurrence_id=None,
		recurrence_total=None,
		recurrence_count=None,
		bunq_payment_id=None,
		import_hash_v2=None,
		sepa_cc=None,
		sepa_ct_op=None,
		sepa_ct_id=None,
		sepa_db=None,
		sepa_country=None,
		sepa_ep=None,
		sepa_ci=None,
		sepa_batch_id=None,
		date=datetime.now(timezone.utc),
		type=TransactionTypeProperty.withdrawal,
		latitude=None,
		longitude=None,
		zoom_level=None,
		has_attachments=False,
	)


@pytest.fixture
def sample_firefly_transaction(sample_transaction_split: TransactionSplit) -> FireflyTransaction:
	"""Sample Firefly transaction attributes for testing"""
	return FireflyTransaction(
		created_at=datetime.now(timezone.utc),
		updated_at=datetime.now(timezone.utc),
		user='1',
		group_title='Test Transaction Group',
		transactions=[sample_transaction_split],
	)


@pytest.fixture
def sample_transaction_read(sample_firefly_transaction: FireflyTransaction) -> TransactionRead:
	"""Sample TransactionRead object for testing"""
	return TransactionRead(
		id='456',
		type='transactions',
		attributes=sample_firefly_transaction,
		links=ObjectLink(),
	)


@pytest.fixture
def sample_transaction_single(sample_transaction_read: TransactionRead) -> TransactionSingle:
	"""Sample TransactionSingle for testing"""
	return TransactionSingle(data=sample_transaction_read)


@pytest.fixture
def sample_transaction_array(sample_transaction_read: TransactionRead) -> TransactionArray:
	"""Sample TransactionArray for testing"""
	return TransactionArray(
		data=[sample_transaction_read],
		meta=Meta(
			pagination=Pagination(total=1, count=1, per_page=50, current_page=1, total_pages=1)
		),
		links=PageLink(),
	)


@pytest.fixture
def mock_httpx_client():
	"""Mock httpx AsyncClient for testing"""
	client = AsyncMock()
	response = MagicMock()
	response.json.return_value = {'data': []}
	response.raise_for_status.return_value = None
	client.get.return_value = response
	client.post.return_value = response
	return client


@pytest.fixture
def sample_firefly_budget() -> FireflyBudget:
	"""Sample Firefly Budget attributes for testing"""
	return FireflyBudget(
		name='Groceries',
		active=True,
		notes='Monthly grocery budget',
		order=1,
	)


@pytest.fixture
def sample_budget_read(sample_firefly_budget: FireflyBudget) -> BudgetRead:
	"""Sample BudgetRead object for testing"""
	return BudgetRead(id='789', type='budgets', attributes=sample_firefly_budget)


@pytest.fixture
def sample_budget_array(sample_budget_read: BudgetRead) -> BudgetArray:
	"""Sample BudgetArray for testing"""
	return BudgetArray(
		data=[sample_budget_read],
		meta=Meta(
			pagination=Pagination(total=1, count=1, per_page=10, current_page=1, total_pages=1)
		),
	)


@pytest.fixture
def sample_budget(sample_budget_read: BudgetRead) -> Budget:
	"""Sample Budget model for testing"""
	return Budget.from_budget_read(sample_budget_read)
