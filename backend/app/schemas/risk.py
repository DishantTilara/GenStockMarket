import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TradeSetupResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    side: str  # BUY, SELL
    entry_zone: Dict[str, Decimal]  # {"min": 100, "max": 102}
    stop_loss: Decimal
    target_price: Decimal
    quantity: int
    risk_amount: Decimal
    risk_reward: Decimal
    reasons: List[str]
    invalidation: List[str]
    status: str
    data_timestamp: datetime


class RiskValidationRequest(BaseModel):
    symbol: str
    side: str
    order_type: str = "LIMIT"
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    stop_loss: Optional[Decimal] = None
    target: Optional[Decimal] = None


class RiskCheckItem(BaseModel):
    check_name: str
    passed: bool
    message: str


class RiskValidationResponse(BaseModel):
    approved: bool
    rejection_code: Optional[str] = None
    rejection_reason: Optional[str] = None
    checks: List[RiskCheckItem]
    confirmation_token: Optional[str] = None


class OrderExecuteRequest(BaseModel):
    confirmation_token: str
    symbol: str
    side: str
    order_type: str
    quantity: int
    price: Decimal
    stop_loss: Optional[Decimal] = None
    target: Optional[Decimal] = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    side: str
    order_type: str
    quantity: int
    price: Decimal
    status: str
    broker_order_id: Optional[str] = None
    created_at: datetime
