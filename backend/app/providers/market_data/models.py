from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional


@dataclass
class MarketQuote:
    """Normalized real-time quote for an Indian stock or index."""
    symbol: str
    exchange: str
    provider_symbol: str
    timestamp: datetime
    price: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    previous_close: Decimal
    volume: int
    change: Decimal = Decimal("0.00")
    change_pct: Decimal = Decimal("0.00")
    freshness: str = "FRESH"  # FRESH, STALE, INVALID
    market_session: str = "OPEN"  # OPEN, PRE_OPEN, CLOSED
    quality: str = "HIGH"

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        if self.change == Decimal("0.00") and self.previous_close and self.previous_close > 0:
            self.change = round(self.price - self.previous_close, 2)
            self.change_pct = round((self.change / self.previous_close) * Decimal("100"), 2)

    def to_dict(self) -> Dict[str, Any]:
        """Return dict suitable for internal domain services."""
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "provider_symbol": self.provider_symbol,
            "price": self.price,
            "change": self.change,
            "change_pct": self.change_pct,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.price,
            "prev_close": self.previous_close,
            "previous_close": self.previous_close,
            "volume": self.volume,
            "timestamp": self.timestamp,
            "freshness": self.freshness,
            "market_session": self.market_session,
            "quality": self.quality,
        }

    def to_serializable_dict(self) -> Dict[str, Any]:
        """Return JSON-serializable dict for Redis and WebSocket transmission."""
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "provider_symbol": self.provider_symbol,
            "price": float(self.price),
            "change": float(self.change),
            "change_pct": float(self.change_pct),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.price),
            "prev_close": float(self.previous_close),
            "volume": int(self.volume),
            "timestamp": self.timestamp.isoformat(),
            "freshness": self.freshness,
            "market_session": self.market_session,
            "quality": self.quality,
        }


@dataclass
class CandleBarData:
    """Normalized candlestick bar (1m, 5m, 15m, 1h, 1d)."""
    symbol: str
    interval_start: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    timeframe: str = "1m"
    source: str = "yfinance"
    quality: str = "HIGH"

    def __post_init__(self):
        if self.interval_start.tzinfo is None:
            self.interval_start = self.interval_start.replace(tzinfo=timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "interval_start": self.interval_start,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timeframe": self.timeframe,
            "source": self.source,
            "quality": self.quality,
        }

    def to_serializable_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "interval_start": self.interval_start.isoformat(),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "volume": int(self.volume),
            "timeframe": self.timeframe,
            "source": self.source,
            "quality": self.quality,
        }


@dataclass
class MarketStatusInfo:
    """Trading session awareness for Indian markets (Asia/Kolkata)."""
    status: str  # OPEN, PRE_OPEN, CLOSED
    exchange: str  # NSE
    trading_day: str
    market_time: datetime
    message: str
    is_open: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "exchange": self.exchange,
            "trading_day": self.trading_day,
            "market_time": self.market_time.isoformat(),
            "message": self.message,
            "is_open": self.is_open,
        }
