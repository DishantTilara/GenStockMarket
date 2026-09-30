import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    timeframe: str = "5m"
    entry_rules: List[str]
    exit_rules: List[str] = []
    stop_loss: Dict[str, Any]  # {"type": "pct", "value": 1.5}
    target: Dict[str, Any]     # {"type": "pct", "value": 3.0}


class StrategyResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    timeframe: str
    entry_rules: List[str]
    exit_rules: List[str]
    stop_loss: Dict[str, Any]
    target: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BacktestRequest(BaseModel):
    strategy_id: Optional[uuid.UUID] = None
    symbol: str
    timeframe: str = "5m"
    days_back: int = Field(default=30, ge=1, le=365)
    initial_capital: Decimal = Field(default=Decimal("100000.00"), gt=0)
    slippage_pct: Decimal = Field(default=Decimal("0.05"), ge=0)
    brokerage_per_trade: Decimal = Field(default=Decimal("20.00"), ge=0)
    entry_rules: Optional[List[str]] = None
    exit_rules: Optional[List[str]] = None
    stop_loss_pct: Optional[Decimal] = Decimal("1.5")
    target_pct: Optional[Decimal] = Decimal("3.0")


class BacktestTradeResponse(BaseModel):
    entry_time: datetime
    exit_time: datetime
    side: str
    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    pnl: Decimal
    pnl_pct: Decimal
    exit_reason: str


class BacktestResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    timeframe: str
    initial_capital: Decimal
    total_return: Decimal
    cagr: Decimal
    win_rate: Decimal
    loss_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    trade_count: int
    trades: List[BacktestTradeResponse] = []
    equity_curve: List[Dict[str, Any]] = []
    status: str
    created_at: datetime
