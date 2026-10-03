import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    id: uuid.UUID
    available_balance: Decimal
    locked_balance: Decimal
    total_balance: Decimal
    currency: str

    class Config:
        from_attributes = True


class DepositRequestCreate(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    idempotency_key: str = Field(..., min_length=8)
    payment_method: str = "simulated_upi"


class DepositResponse(BaseModel):
    deposit_id: uuid.UUID
    wallet_id: uuid.UUID
    amount: Decimal
    status: str
    reference_id: Optional[str] = None
    message: str


class WithdrawalRequestCreate(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    bank_account_info: str = Field(..., min_length=4)


class WithdrawalResponse(BaseModel):
    withdrawal_id: uuid.UUID
    amount: Decimal
    status: str
    reference_id: Optional[str] = None
    message: str


class LedgerEntryResponse(BaseModel):
    id: uuid.UUID
    reference: str
    entry_type: str
    direction: str
    amount: Decimal
    balance_after: Decimal
    status: str
    description: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
