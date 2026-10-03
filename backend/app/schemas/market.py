import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class InstrumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    name: str
    exchange: str
    segment: str
    isin: Optional[str] = None
    lot_size: int
    tick_size: Decimal
    sector: Optional[str] = None
    provider_symbol: Optional[str] = None
    is_active: bool


class InstrumentSearchResponse(BaseModel):
    symbol: str
    exchange: str
    name: str
    provider_symbol: str
    sector: Optional[str] = None


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
    exchange: Optional[str] = "NSE"
    provider_symbol: Optional[str] = None
    freshness: Optional[str] = "FRESH"
    market_session: Optional[str] = "OPEN"
    quality: str = "HIGH"


class CandleBarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interval_start: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    is_complete: bool = True
    quality: str = "HIGH"


class MarketStatusResponse(BaseModel):
    status: str  # OPEN, CLOSED, PRE_OPEN
    exchange: str = "NSE"
    trading_day: str
    market_time: datetime
    message: str
    is_open: Optional[bool] = None


class MarketHealthResponse(BaseModel):
    provider: str
    status: Optional[str] = "HEALTHY"
    last_event: Optional[str] = None
    last_completed_minute: Optional[str] = None
    ingestion_lag_seconds: float = 0.0
    symbols_expected: int = 0
    symbols_received: int = 0
    missing_minutes: int = 0
    reconnect_count: int = 0
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    latency_ms: Optional[float] = 0.0
    consecutive_failures: Optional[int] = 0


class StatementRow(BaseModel):
    metric: str
    values: Dict[str, Optional[float]] = {}


class FundamentalsResponse(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: Optional[str] = "INR"
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    eps: Optional[float] = None
    book_value: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    dividend_rate: Optional[float] = None
    total_debt: Optional[float] = None
    debt_to_equity: Optional[float] = None
    total_revenue: Optional[float] = None
    net_income: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    income_statement: Optional[List[StatementRow]] = None
    balance_sheet: Optional[List[StatementRow]] = None
    cashflow_statement: Optional[List[StatementRow]] = None
    provider: str = "yfinance"
    timestamp: datetime

