import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class PortfolioPositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    sector: Optional[str] = None
    quantity: int
    average_price: Decimal
    current_price: Decimal
    invested_amount: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    realized_pnl: Decimal = Decimal("0.00")
    stop_loss: Optional[Decimal] = None
    target_price: Optional[Decimal] = None


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    total_invested: Decimal
    current_value: Decimal
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_pct: Decimal
    realized_pnl: Decimal = Decimal("0.00")
    total_pnl: Decimal = Decimal("0.00")
    today_pnl: Decimal = Decimal("0.00")
    today_pnl_pct: Decimal = Decimal("0.00")
    cash_balance: Decimal
    total_equity: Decimal
    positions: List[PortfolioPositionResponse] = []
    sector_allocation: Dict[str, Decimal] = {}


class PortfolioAnalysisResponse(BaseModel):
    summary: str
    largest_contributors: List[Dict[str, Any]]
    largest_detractors: List[Dict[str, Any]]
    concentration_risks: List[str]
    sector_exposure: Dict[str, float]
    diversification_observations: List[str]
    disclaimer: str = "This analysis is deterministic and analytical. Past performance does not guarantee future results."
