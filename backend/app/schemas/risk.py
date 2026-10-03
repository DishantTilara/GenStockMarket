import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TradeSetupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    price: Optional[Decimal] = None
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


class OrderCreateRequest(BaseModel):
    symbol: str
    side: str  # BUY, SELL
    order_type: str = "MARKET"  # MARKET, LIMIT, SL, SL_LIMIT
    quantity: int = Field(..., gt=0)
    price: Optional[Decimal] = None
    limit_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    target_price: Optional[Decimal] = None
    idempotency_key: Optional[str] = None
    confirmation_token: Optional[str] = None


class OrderModifyRequest(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=Decimal("0"))
    stop_loss: Optional[Decimal] = None
    target_price: Optional[Decimal] = None


class OrderEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    event_type: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    side: str
    order_type: str
    quantity: int
    price: Decimal
    execution_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    target: Optional[Decimal] = None
    status: str
    charges: Optional[Decimal] = Decimal("0.00")
    realized_pnl: Optional[Decimal] = None
    error_message: Optional[str] = None
    broker_order_id: Optional[str] = None
    created_at: datetime


class OrderDetailResponse(OrderResponse):
    events: Optional[List[OrderEventResponse]] = None


class PaperResetRequest(BaseModel):
    clear_history: bool = True
    confirm: bool = True

