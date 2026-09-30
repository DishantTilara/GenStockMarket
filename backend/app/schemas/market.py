import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class InstrumentResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    exchange: str
    segment: str
    isin: Optional[str] = None
    lot_size: int
    tick_size: Decimal
    sector: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class QuoteResponse(BaseModel):
    symbol: str
    price: Decimal
    change: Decimal = Decimal("0.0")
    change_pct: Decimal = Decimal("0.0")
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    volume: int = 0
    timestamp: datetime
    quality: str = "HIGH"


class CandleBarResponse(BaseModel):
    interval_start: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    is_complete: bool
    quality: str = "HIGH"

    class Config:
        from_attributes = True


class MarketStatusResponse(BaseModel):
    status: str  # OPEN, CLOSED, PRE_OPEN
    exchange: str = "NSE"
    trading_day: str
    market_time: datetime
    message: str


class MarketHealthResponse(BaseModel):
    provider: str
    last_event: Optional[str] = None
    last_completed_minute: Optional[str] = None
    ingestion_lag_seconds: float
    symbols_expected: int
    symbols_received: int
    missing_minutes: int
    reconnect_count: int
