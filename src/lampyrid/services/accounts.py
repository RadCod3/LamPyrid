"""Account Service for LamPyrid.

This service handles account-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

from typing import List

from ..clients.firefly import FireflyClient
from ..models.firefly_models import AccountStore
from ..models.lampyrid_models import (
	Account,
	GetAccountRequest,
	ListAccountRequest,
	SearchAccountRequest,
)


class AccountService:
	"""Service for managing Firefly III accounts.

	This service provides a high-level interface for account operations,
	handling model conversion and business logic while delegating
	HTTP operations to the FireflyClient.
	"""

	def __init__(self, client: FireflyClient) -> None:
		"""Initialize the account service with a FireflyClient instance."""
		self._client = client

	async def list_accounts(self, req: ListAccountRequest) -> List[Account]:
		"""List accounts with optional type filtering.

		Args:
			req: Request containing account type filter

		Returns:
			List of accounts matching the filter criteria

		"""
		account_array = await self._client.list_accounts(type=req.type)

		return [Account.from_account_read(account_read) for account_read in account_array.data]

	async def get_account(self, req: GetAccountRequest) -> Account:
		"""Get detailed information for a single account.

		Args:
			req: Request containing the account ID

		Returns:
			Account details including balance and metadata

		"""
		account_single = await self._client.get_account(req.id)
		return Account.from_account_read(account_single.data)

	async def search_accounts(self, req: SearchAccountRequest) -> List[Account]:
		"""Search accounts by name with optional type filtering.

		Args:
			req: Request containing search query and type filter

		Returns:
			List of accounts matching the search criteria

		"""
		account_array = await self._client.search_accounts(req.query, req.type)

		return [Account.from_account_read(account_read) for account_read in account_array.data]

	async def create_account(self, account_store: AccountStore) -> Account:
		"""Create a new account.

		Args:
			account_store: Account data for creation

		Returns:
			Created account details

		"""
		account_single = await self._client.create_account(account_store)
		return Account.from_account_read(account_single.data)
