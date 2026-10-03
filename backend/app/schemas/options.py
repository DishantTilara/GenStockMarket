from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class OptionContract(BaseModel):
    contract_symbol: Optional[str] = None
    strike: float
    last_price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = 0
    open_interest: Optional[int] = 0
    implied_volatility: Optional[float] = None
    in_the_money: bool = False


class OptionChainRow(BaseModel):
    strike: float
    call: Optional[OptionContract] = None
    put: Optional[OptionContract] = None


class OptionChainResponse(BaseModel):
    symbol: str
    underlying_price: float
    expiries: List[str]
    selected_expiry: str
    chain: List[OptionChainRow]
    total_call_oi: int = 0
    total_put_oi: int = 0
    pcr_ratio: Optional[float] = None
    max_pain: Optional[float] = None
    provider: str = "yfinance"
    timestamp: datetime
