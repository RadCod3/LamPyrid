from typing import Optional

from pydantic import BaseModel, Field

from .firefly_models import AccountRead, AccountTypeFilter


class Account(BaseModel):
    id: str = Field(..., examples=["2"])
    name: str = Field(..., examples=["Cash"])
    currency_code: Optional[str] = Field(None, examples=["GBP"])
    current_balance: Optional[float] = Field(None, examples=[1000.0])

    @classmethod
    def from_account_read(cls, account_read: "AccountRead") -> "Account":
        """Create an Account instance from a Firefly AccountRead object."""
        return cls(
            id=account_read.id,
            name=account_read.attributes.name,
            currency_code=account_read.attributes.currency_code,
            current_balance=(
                float(account_read.attributes.current_balance)
                if account_read.attributes.current_balance
                else None
            ),
        )


class ListAccountRequest(BaseModel):
    type: AccountTypeFilter = Field(..., description="Type of account to filter by")
