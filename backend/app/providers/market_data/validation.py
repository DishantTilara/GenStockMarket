import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Tuple, Optional, Dict, Any
from app.providers.market_data.models import MarketQuote, CandleBarData, MarketStatusInfo

logger = logging.getLogger("market_data.validation")


def validate_quote(quote: MarketQuote) -> Tuple[bool, Optional[str]]:
    """
    Validate incoming market quote against integrity rules:
    - symbol exists
    - timestamp exists and is valid
    - price > 0
    - high >= low
    - high >= price (with 0.1% tolerance for fast-moving ticks)
    - low <= price (with 0.1% tolerance)
    - volume >= 0
    """
    if not quote.symbol or not quote.symbol.strip():
        return False, "Symbol is missing or empty"

    if quote.timestamp is None:
        return False, "Timestamp is missing"

    now_utc = datetime.now(timezone.utc)
    if quote.timestamp > now_utc + timedelta(minutes=5):
        return False, "Timestamp is excessively in the future"

    try:
        price = Decimal(str(quote.price))
        if price <= Decimal("0.00"):
            return False, f"Price must be positive, got {price}"
    except Exception:
        return False, "Invalid price numeric value"

    try:
        high = Decimal(str(quote.high))
        low = Decimal(str(quote.low))
        if high < low:
            return False, f"High ({high}) is less than Low ({low})"
        
        # High and low bounds against price with 0.5% buffer for tick arrivals
        if high * Decimal("1.005") < price:
            return False, f"Price ({price}) significantly exceeds High ({high})"
        if low * Decimal("0.995") > price:
            return False, f"Price ({price}) significantly below Low ({low})"
    except Exception:
        return False, "Invalid high/low numeric values"

    if quote.volume < 0:
        return False, f"Volume cannot be negative, got {quote.volume}"

    return True, None


def validate_candle(candle: Any) -> Tuple[bool, Optional[str]]:
    """Validate candlestick OHLCV bar integrity."""
    if isinstance(candle, dict):
        sym = candle.get("symbol")
        ts = candle.get("interval_start")
        o = candle.get("open")
        h = candle.get("high")
        l = candle.get("low")
        c = candle.get("close")
        v = candle.get("volume", 0)
    else:
        sym = getattr(candle, "symbol", None)
        ts = getattr(candle, "interval_start", None)
        o = getattr(candle, "open", None)
        h = getattr(candle, "high", None)
        l = getattr(candle, "low", None)
        c = getattr(candle, "close", None)
        v = getattr(candle, "volume", 0)

    if not sym:
        return False, "Candle symbol missing"
    if not ts:
        return False, "Candle interval_start missing"

    try:
        o_dec = Decimal(str(o))
        h_dec = Decimal(str(h))
        l_dec = Decimal(str(l))
        c_dec = Decimal(str(c))
        v_int = int(v)

        if o_dec <= 0 or h_dec <= 0 or l_dec <= 0 or c_dec <= 0:
            return False, "Candle OHLC prices must all be positive"
        if h_dec < l_dec:
            return False, f"Candle High ({h_dec}) < Low ({l_dec})"
        if v_int < 0:
            return False, f"Candle volume cannot be negative ({v_int})"
    except Exception as exc:
        return False, f"Invalid candle numeric values: {exc}"

    return True, None


def calculate_freshness(
    timestamp_or_quote: Any,
    market_session: Optional[str] = None,
    max_age_seconds: int = 120,
    reference_now: Optional[datetime] = None
) -> str:
    """
    Determine quote freshness status:
    - FRESH: Recent tick received within max_age_seconds during open/active session
    - STALE: Quote is older than max_age_seconds
    - INVALID: Null or unparseable timestamp
    """
    if timestamp_or_quote is None:
        return "INVALID"

    if isinstance(timestamp_or_quote, MarketQuote):
        timestamp = timestamp_or_quote.timestamp
        market_session = market_session or timestamp_or_quote.market_session or "OPEN"
    else:
        timestamp = timestamp_or_quote
        market_session = market_session or "OPEN"

    if timestamp is None:
        return "INVALID"

    now_utc = reference_now or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    age_seconds = (now_utc - timestamp).total_seconds()
    if age_seconds < -300:  # Excessively in future
        return "INVALID"

    if market_session == "CLOSED":
        # Outside trading hours, data reflects last traded price rather than active ticks
        return "STALE"

    if age_seconds <= max_age_seconds:
        return "FRESH"
    return "STALE"


def get_indian_market_status(reference_time: Optional[datetime] = None) -> MarketStatusInfo:
    """
    Determine Indian Market (NSE/BSE) trading session status based on IST (Asia/Kolkata, UTC+5:30).
    - PRE_OPEN: 09:00 - 09:15 IST (Mon-Fri)
    - OPEN: 09:15 - 15:30 IST (Mon-Fri)
    - CLOSED: Weekends, before 09:00 IST, or after 15:30 IST
    """
    ref_utc = reference_time or datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = ref_utc + ist_offset
    weekday = now_ist.weekday()  # 0=Monday, 6=Sunday

    if weekday >= 5:
        return MarketStatusInfo(
            status="CLOSED",
            exchange="NSE",
            trading_day=now_ist.strftime("%Y-%m-%d"),
            market_time=now_ist,
            message="Exchange closed for weekend",
            is_open=False
        )

    minutes_from_midnight = now_ist.hour * 60 + now_ist.minute
    if 540 <= minutes_from_midnight < 555:  # 09:00 to 09:15
        return MarketStatusInfo(
            status="PRE_OPEN",
            exchange="NSE",
            trading_day=now_ist.strftime("%Y-%m-%d"),
            market_time=now_ist,
            message="NSE Pre-market order collection and discovery",
            is_open=False
        )
    elif 555 <= minutes_from_midnight < 930:  # 09:15 to 15:30
        return MarketStatusInfo(
            status="OPEN",
            exchange="NSE",
            trading_day=now_ist.strftime("%Y-%m-%d"),
            market_time=now_ist,
            message="Normal trading session active",
            is_open=True
        )
    else:
        return MarketStatusInfo(
            status="CLOSED",
            exchange="NSE",
            trading_day=now_ist.strftime("%Y-%m-%d"),
            market_time=now_ist,
            message="Market closed (Normal trading 09:15 - 15:30 IST)",
            is_open=False
        )
