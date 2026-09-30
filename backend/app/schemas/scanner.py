import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class ScannerRule(BaseModel):
    indicator: str  # EMA, SMA, RSI, MACD, VOLUME, PRICE, VWAP
    operator: str   # >, <, >=, <=, CROSS_ABOVE, CROSS_BELOW, BETWEEN
    value: Union[float, str, List[float]]
    params: Optional[Dict[str, Any]] = None


class ScannerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rules: List[ScannerRule]
    is_public: bool = False


class ScannerResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    rules: List[Dict[str, Any]]
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResultItem(BaseModel):
    symbol: str
    name: str
    price: Decimal
    change_pct: Decimal
    volume: int
    matched_conditions: List[str]
    metrics: Dict[str, Any]


class ScannerNLQueryRequest(BaseModel):
    query: str = Field(..., min_length=5, description="Natural language scanner prompt")
