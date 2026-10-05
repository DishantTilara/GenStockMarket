import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import AsyncGenerator, Dict, List, Any, Optional

import pandas as pd
import yfinance as yf

from app.core.config import settings
from app.providers.market_data.base import MarketDataProvider
from app.providers.market_data.models import MarketQuote, CandleBarData
from app.providers.market_data.symbol_mapper import IndianSymbolMapper
from app.providers.market_data.validation import (
    validate_quote,
    validate_candle,
    calculate_freshness,
    get_indian_market_status,
)

logger = logging.getLogger("market_data.yfinance_provider")

DEFAULT_INSTRUMENTS: List[Dict[str, Any]] = [
    {"symbol": "NIFTY 50", "name": "Nifty 50 Index", "exchange": "NSE", "segment": "INDEX", "provider_symbol": "^NSEI", "sector": "Benchmark", "lot_size": 25, "tick_size": 0.05},
    {"symbol": "BANKNIFTY", "name": "Nifty Bank Index", "exchange": "NSE", "segment": "INDEX", "provider_symbol": "^NSEBANK", "sector": "Banking", "lot_size": 15, "tick_size": 0.05},
    {"symbol": "SENSEX", "name": "BSE Sensex Index", "exchange": "BSE", "segment": "INDEX", "provider_symbol": "^BSESN", "sector": "Benchmark", "lot_size": 10, "tick_size": 0.05},
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "RELIANCE.NS", "sector": "Energy", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "TCS.NS", "sector": "IT", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "HDFCBANK.NS", "sector": "Banking", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "INFY", "name": "Infosys Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "INFY.NS", "sector": "IT", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "ICICIBANK.NS", "sector": "Banking", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "BHARTIARTL.NS", "sector": "Telecom", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "SBIN", "name": "State Bank of India", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "SBIN.NS", "sector": "Banking", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "ITC", "name": "ITC Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "ITC.NS", "sector": "FMCG", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "LT.NS", "sector": "Capital Goods", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "TATAMOTORS.NS", "sector": "Automobile", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "HINDUNILVR.NS", "sector": "FMCG", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "BAJFINANCE.NS", "sector": "Financial Services", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "exchange": "NSE", "segment": "EQUITY", "provider_symbol": "SUNPHARMA.NS", "sector": "Healthcare", "lot_size": 1, "tick_size": 0.05},
]


class YFinanceMarketDataProvider(MarketDataProvider):
    """
    Production-style Yahoo Finance Market Data Provider for Indian Markets.
    - Centralized symbol mapping (e.g. RELIANCE -> RELIANCE.NS)
    - Normalized internal domain models (MarketQuote, CandleBarData)
    - Thread-pool offloaded network requests via asyncio.to_thread
    - Comprehensive data validation and freshness evaluation
    - Resilient health monitoring and error containment
    """

    def __init__(self):
        self._connected = False
        self._running = False
        self._last_success: Optional[datetime] = None
        self._last_failure: Optional[datetime] = None
        self._last_quote_timestamp: Optional[datetime] = None
        self._last_latency_ms: float = 0.0
        self._consecutive_failures: int = 0
        self._cache_quotes: Dict[str, MarketQuote] = {}
        self._poll_interval = float(getattr(settings, "MARKET_POLL_INTERVAL_SECONDS", 30.0))
        self._max_age_seconds = int(getattr(settings, "MARKET_DATA_MAX_AGE_SECONDS", 120))

    async def connect(self) -> None:
        self._connected = True
        self._running = True
        logger.info("[YFINANCE] Connected to YFinance market data provider.")

    async def close(self) -> None:
        self._running = False
        self._connected = False
        logger.info("[YFINANCE] Connection closed.")

    def get_health(self) -> Dict[str, Any]:
        """Return provider health status metrics."""
        if self._consecutive_failures == 0:
            status = "HEALTHY"
        elif self._consecutive_failures < 3:
            status = "DEGRADED"
        else:
            status = "DOWN"

        return {
            "provider": "yfinance",
            "status": status,
            "is_connected": self._connected,
            "last_success": self._last_success.isoformat() if self._last_success else None,
            "last_failure": self._last_failure.isoformat() if self._last_failure else None,
            "last_quote_timestamp": self._last_quote_timestamp.isoformat() if self._last_quote_timestamp else None,
            "latency_ms": round(self._last_latency_ms, 2),
            "consecutive_failures": self._consecutive_failures,
        }

    async def get_instruments(self) -> List[Dict[str, Any]]:
        return DEFAULT_INSTRUMENTS

    async def market_status(self) -> Dict[str, Any]:
        info = get_indian_market_status()
        return info.to_dict()

    def _sync_fetch_quote(self, symbol: str) -> Optional[MarketQuote]:
        """Synchronously query yfinance for a single symbol (runs in thread pool)."""
        provider_sym = IndianSymbolMapper.to_provider_symbol(symbol)
        canonical_sym, exchange = IndianSymbolMapper.to_canonical_symbol(provider_sym)

        t_start = time.perf_counter()
        try:
            ticker = yf.Ticker(provider_sym)
            fast = getattr(ticker, "fast_info", None)
            
            # 1. Try fast_info
            price = None
            open_p = None
            high = None
            low = None
            prev_close = None
            volume = 0
            ts = None

            if fast is not None:
                try:
                    def _get_val(obj, *keys):
                        for k in keys:
                            if isinstance(obj, dict) and k in obj:
                                val = obj[k]
                                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                                    return val
                            val = getattr(obj, k, None)
                            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                                return val
                        return None

                    price = _get_val(fast, "last_price", "lastPrice", "regular_market_price", "regularMarketPrice", "currentPrice")
                    prev_close = _get_val(fast, "previous_close", "previousClose", "regularMarketPreviousClose")
                    open_p = _get_val(fast, "open", "regularMarketOpen")
                    high = _get_val(fast, "day_high", "dayHigh", "regularMarketDayHigh")
                    low = _get_val(fast, "day_low", "dayLow", "regularMarketDayLow")
                    vol_val = _get_val(fast, "last_volume", "lastVolume", "regularMarketVolume")
                    volume = int(vol_val) if vol_val is not None else 0
                except Exception:
                    pass

            # 2. Fallback to 1-day/1-minute history if fast_info missing or incomplete
            if price is None or price <= 0:
                try:
                    df = ticker.history(period="1d", interval="1m")
                    if df is not None and not df.empty:
                        last_row = df.iloc[-1]
                        price = float(last_row["Close"])
                        open_p = float(df.iloc[0]["Open"])
                        high = float(df["High"].max())
                        low = float(df["Low"].min())
                        volume = int(df["Volume"].sum())
                        
                        idx_val = df.index[-1]
                        if hasattr(idx_val, "to_pydatetime"):
                            ts = idx_val.to_pydatetime()
                        elif isinstance(idx_val, datetime):
                            ts = idx_val
                except Exception:
                    pass

            # 3. Fallback to daily history (essential for indices like ^NSEI, ^NSEBANK which have no 1m bars on YF)
            if price is None or price <= 0:
                try:
                    df_daily = ticker.history(period="5d", interval="1d")
                    if df_daily is not None and not df_daily.empty:
                        last_row = df_daily.iloc[-1]
                        price = float(last_row["Close"])
                        open_p = float(last_row["Open"]) if open_p is None else open_p
                        high = float(last_row["High"]) if high is None else high
                        low = float(last_row["Low"]) if low is None else low
                        if prev_close is None:
                            prev_close = float(df_daily.iloc[-2]["Close"]) if len(df_daily) > 1 else price
                        vol_val = last_row.get("Volume", 0)
                        volume = int(vol_val) if not pd.isna(vol_val) else 0
                        idx_val = df_daily.index[-1]
                        if hasattr(idx_val, "to_pydatetime"):
                            ts = idx_val.to_pydatetime()
                        elif isinstance(idx_val, datetime):
                            ts = idx_val
                except Exception:
                    pass

            # Fallback for previous close if not available
            if prev_close is None and price is not None:
                prev_close = price

            if price is None or price <= 0:
                logger.warning(f"[YFINANCE] Could not retrieve price for {provider_sym}")
                return None

            open_p = open_p if open_p is not None and open_p > 0 else price
            high = high if high is not None and high >= price else price
            low = low if low is not None and 0 < low <= price else price
            prev_close = prev_close if prev_close is not None and prev_close > 0 else price

            # Resolve timestamp from provider
            if ts is None:
                ts = datetime.now(timezone.utc)
            elif ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)

            session_info = get_indian_market_status(ts)
            freshness = calculate_freshness(ts, session_info.status, self._max_age_seconds)

            quote = MarketQuote(
                symbol=canonical_sym,
                exchange=exchange,
                provider_symbol=provider_sym,
                timestamp=ts,
                price=Decimal(str(round(price, 2))),
                open=Decimal(str(round(open_p, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                previous_close=Decimal(str(round(prev_close, 2))),
                volume=volume,
                freshness=freshness,
                market_session=session_info.status,
                quality="HIGH"
            )

            is_valid, reason = validate_quote(quote)
            if not is_valid:
                logger.warning(f"[YFINANCE] Quote validation failed for {symbol}: {reason}")
                quote.freshness = "INVALID"

            latency_ms = (time.perf_counter() - t_start) * 1000
            self._last_latency_ms = latency_ms
            self._last_success = datetime.now(timezone.utc)
            self._last_quote_timestamp = ts
            self._consecutive_failures = 0

            logger.info(f"[YFINANCE] {provider_sym} fetched successfully (LTP: ₹{quote.price}, latency: {latency_ms:.1f}ms)")
            return quote

        except Exception as exc:
            self._last_failure = datetime.now(timezone.utc)
            self._consecutive_failures += 1
            logger.error(f"[YFINANCE] Failed to fetch {provider_sym}: {exc}")
            return None

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Retrieve latest validated quote for symbol."""
        quote = await asyncio.to_thread(self._sync_fetch_quote, symbol)
        if quote:
            self._cache_quotes[quote.symbol] = quote
            return quote.to_dict()

        # If fetch fails, check memory cache for graceful fallback
        canonical, _ = IndianSymbolMapper.to_canonical_symbol(symbol)
        if canonical in self._cache_quotes:
            cached = self._cache_quotes[canonical]
            cached.freshness = "STALE"
            return cached.to_dict()

        # Realistic fallback default quote if remote fetch is unreachable
        logger.warning(f"[YFINANCE] No quote available for {symbol}, using fallback structure")
        now = datetime.now(timezone.utc)
        base_prices: Dict[str, Decimal] = {
            "NIFTY 50": Decimal("22550.00"),
            "BANKNIFTY": Decimal("48200.00"),
            "SENSEX": Decimal("74500.00"),
            "INDIA VIX": Decimal("13.50"),
            "RELIANCE": Decimal("1176.00"),
            "TCS": Decimal("4260.00"),
            "HDFCBANK": Decimal("1680.00"),
            "INFY": Decimal("1910.00"),
            "ICICIBANK": Decimal("1240.00"),
            "TATAMOTORS": Decimal("980.00"),
            "SBIN": Decimal("810.00"),
            "BHARTIARTL": Decimal("1480.00"),
            "ITC": Decimal("510.00"),
            "LT": Decimal("3740.00"),
            "HINDUNILVR": Decimal("2380.00"),
            "BAJFINANCE": Decimal("6850.00"),
            "SUNPHARMA": Decimal("1750.00")
        }
        base_p = base_prices.get(canonical, Decimal("1000.00"))
        return {
            "symbol": canonical,
            "exchange": "NSE",
            "provider_symbol": IndianSymbolMapper.to_provider_symbol(symbol),
            "price": base_p,
            "change": Decimal("0.00"),
            "change_pct": Decimal("0.00"),
            "open": base_p,
            "high": base_p,
            "low": base_p,
            "close": base_p,
            "prev_close": base_p,
            "volume": 0,
            "timestamp": now,
            "freshness": "STALE",
            "market_session": "OPEN",
            "quality": "LOW"
        }

    def _sync_fetch_candles(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Synchronously query yfinance historical interval bars."""
        provider_sym = IndianSymbolMapper.to_provider_symbol(symbol)
        canonical_sym, _ = IndianSymbolMapper.to_canonical_symbol(provider_sym)

        # Map interval and period
        tf_lower = timeframe.lower()
        if tf_lower in ["1m", "1min", "1"]:
            interval = "1m"
            period = "5d"
        elif tf_lower in ["5m", "5min", "5"]:
            interval = "5m"
            period = "1mo"
        elif tf_lower in ["15m", "15min", "15"]:
            interval = "15m"
            period = "1mo"
        elif tf_lower in ["1h", "60m", "60"]:
            interval = "1h"
            period = "3mo"
        elif tf_lower in ["1d", "day", "daily"]:
            interval = "1d"
            period = "1y"
        else:
            interval = "1m"
            period = "5d"

        try:
            ticker = yf.Ticker(provider_sym)
            df = None

            if start and end and interval == "1d":
                end_inclusive = end + timedelta(days=1)
                df = ticker.history(start=start.strftime("%Y-%m-%d"), end=end_inclusive.strftime("%Y-%m-%d"), interval="1d")
            elif interval in ["1m", "5m", "15m", "30m", "1h"]:
                # For intraday intervals, yfinance period is reliable and doesn't suffer from start==end bug
                intraday_period = "5d" if interval != "1m" else "1d"
                df = ticker.history(period=intraday_period, interval=interval)
                if df is not None and not df.empty and (start or end):
                    try:
                        if df.index.tz is None:
                            df.index = df.index.tz_localize("UTC")
                        else:
                            df.index = df.index.tz_convert("UTC")
                        if start:
                            s_utc = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
                            df = df[df.index >= s_utc]
                        if end:
                            e_utc = end if end.tzinfo else end.replace(tzinfo=timezone.utc)
                            df = df[df.index <= e_utc]
                    except Exception:
                        pass
            else:
                df = ticker.history(period=period, interval=interval)

            # Fallback if empty (e.g. index with no 1m intraday, fallback to 5d daily)
            if df is None or df.empty:
                df = ticker.history(period="5d", interval="1d" if interval in ["1d", "1m"] else interval)

            if df is None or df.empty:
                return []

            bars: List[Dict[str, Any]] = []
            for idx, row in df.iterrows():
                # Handle pandas timestamp
                if hasattr(idx, "to_pydatetime"):
                    bar_ts = idx.to_pydatetime()
                elif isinstance(idx, datetime):
                    bar_ts = idx
                else:
                    continue

                if bar_ts.tzinfo is None:
                    bar_ts = bar_ts.replace(tzinfo=timezone.utc)
                else:
                    bar_ts = bar_ts.astimezone(timezone.utc)

                try:
                    c_open = Decimal(str(round(float(row["Open"]), 2)))
                    c_high = Decimal(str(round(float(row["High"]), 2)))
                    c_low = Decimal(str(round(float(row["Low"]), 2)))
                    c_close = Decimal(str(round(float(row["Close"]), 2)))
                    vol = int(row["Volume"]) if not pd.isna(row["Volume"]) else 0

                    candle_bar = CandleBarData(
                        symbol=canonical_sym,
                        interval_start=bar_ts,
                        open=c_open,
                        high=c_high,
                        low=c_low,
                        close=c_close,
                        volume=vol,
                        timeframe=interval,
                        source="yfinance"
                    )
                    is_valid, _ = validate_candle(candle_bar)
                    if is_valid:
                        bars.append(candle_bar.to_dict())
                except Exception:
                    continue

            return bars[-limit:] if limit else bars

        except Exception as exc:
            logger.error(f"[YFINANCE] Failed fetching candles for {provider_sym}: {exc}")
            return []

    async def get_minute_bars(self, symbol: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Retrieve 1-minute historical candlestick bars between start and end."""
        bars = await asyncio.to_thread(self._sync_fetch_candles, symbol, "1m", 500, start, end)
        return bars

    async def get_candles(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve historical candles for any supported timeframe (1m, 5m, 15m, 1h, 1d)."""
        return await asyncio.to_thread(self._sync_fetch_candles, symbol, timeframe, limit)

    async def get_historical_data(self, symbol: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Retrieve daily bars for symbol."""
        daily_bars = await asyncio.to_thread(self._sync_fetch_candles, symbol, "1d", 365, start, end)
        results = []
        for b in daily_bars:
            results.append({
                "trade_date": b["interval_start"],
                "open": b["open"],
                "high": b["high"],
                "low": b["low"],
                "close": b["close"],
                "volume": b["volume"],
                "vwap": round((b["high"] + b["low"] + b["close"]) / Decimal("3"), 2)
            })
        return results

    async def stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Continuous stream yielding validated ticks for active instruments.
        Polls Yahoo Finance at configured intervals (default 30s) concurrently.
        """
        while self._running:
            try:
                chunk_size = 4
                for i in range(0, len(DEFAULT_INSTRUMENTS), chunk_size):
                    if not self._running:
                        break
                    batch = DEFAULT_INSTRUMENTS[i:i + chunk_size]
                    tasks = [self.get_quote(inst["symbol"]) for inst in batch]
                    quotes = await asyncio.gather(*tasks, return_exceptions=True)

                    for quote in quotes:
                        if isinstance(quote, dict) and "price" in quote:
                            ts = quote.get("timestamp") or datetime.now(timezone.utc)
                            tick = {
                                "symbol": quote["symbol"],
                                "exchange": quote.get("exchange", "NSE"),
                                "provider_symbol": quote.get("provider_symbol"),
                                "price": Decimal(str(quote["price"])),
                                "quantity": max(1, int(quote.get("volume", 100) // 1000) or 50),
                                "timestamp": ts,
                                "change": Decimal(str(quote.get("change", 0.0))),
                                "change_pct": Decimal(str(quote.get("change_pct", 0.0))),
                                "freshness": quote.get("freshness", "FRESH"),
                                "source": "yfinance",
                                "quality": quote.get("quality", "HIGH")
                            }
                            yield tick

                    await asyncio.sleep(0.3)

                # Wait for next polling cycle
                await asyncio.sleep(max(5.0, self._poll_interval))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[YFINANCE] Stream loop encountered error: {e}")
                await asyncio.sleep(5.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[YFINANCE] Stream loop encountered error: {e}")
                await asyncio.sleep(5.0)

    async def health(self) -> Dict[str, Any]:
        return {
            "provider": "yfinance",
            "is_connected": self._running,
            "status": "HEALTHY" if self._running else "CONNECTED",
            "symbols_tracked": len(DEFAULT_INSTRUMENTS),
            "poll_interval": self._poll_interval,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
