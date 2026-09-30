import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    symbol: str
    condition_type: str = Field(..., description="PRICE_ABOVE, PRICE_BELOW, RSI_OVERBOUGHT, RSI_OVERSOLD, VOLUME_SPIKE")
    target_value: Decimal


class AlertResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    condition_type: str
    target_value: Decimal
    is_active: bool
    is_triggered: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertEventResponse(BaseModel):
    id: uuid.UUID
    alert_id: uuid.UUID
    symbol: str
    triggered_price: Decimal
    message: str
    triggered_at: datetime

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WatchlistItemAdd(BaseModel):
    symbol: str
    notes: Optional[str] = None


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    items: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True
