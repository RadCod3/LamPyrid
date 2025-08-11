import httpx
from typing import Any, Dict
from ..config import settings
from ..models.firefly_models import AccountArray, AccountTypeFilter


class FireflyClient:
    def __init__(self) -> None:
        base = str(settings.firefly_base_url).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=base,
            headers={
                "Authorization": f"Bearer {settings.firefly_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def list_accounts(
        self, page: int = 1, type: AccountTypeFilter = AccountTypeFilter.all
    ) -> AccountArray:
        r = await self._client.get(
            "/api/v1/accounts", params={"page": page, "type": type.value}
        )
        r.raise_for_status()
        return AccountArray.model_validate(r.json())

    async def search_accounts(
        self, query: str, page: int = 1, type: AccountTypeFilter = AccountTypeFilter.all
    ) -> AccountArray:
        r = await self._client.get(
            "/api/v1/search/accounts",
            params={"query": query, "page": page, "type": type.value, "field": "name"},
        )
        r.raise_for_status()
        return AccountArray.model_validate(r.json())

    async def search_transactions(self, query: str, page: int = 1) -> Dict[str, Any]:
        r = await self._client.get(
            "/api/v1/transactions", params={"query": query, "page": page}
        )
        r.raise_for_status()
        return r.json()

    async def create_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        r = await self._client.post("/api/v1/transactions", json=payload)
        r.raise_for_status()
        return r.json()

    async def aclose(self) -> None:
        await self._client.aclose()
