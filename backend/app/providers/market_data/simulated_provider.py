import asyncio
import math
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator, Dict, List, Any, Optional
from app.providers.market_data.base import MarketDataProvider

# Default Indian Equities and Indices reference prices
INDIAN_INSTRUMENTS = [
    {"symbol": "NIFTY 50", "name": "Nifty 50 Index", "exchange": "NSE", "segment": "INDEX", "base_price": 25850.00, "sector": "Benchmark", "lot_size": 25, "tick_size": 0.05},
    {"symbol": "BANKNIFTY", "name": "Nifty Bank Index", "exchange": "NSE", "segment": "INDEX", "base_price": 53400.00, "sector": "Banking", "lot_size": 15, "tick_size": 0.05},
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 2985.50, "sector": "Energy", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 4260.00, "sector": "IT", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 1682.25, "sector": "Banking", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "INFY", "name": "Infosys Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 1915.00, "sector": "IT", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 1248.80, "sector": "Banking", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 1654.50, "sector": "Telecom", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "SBIN", "name": "State Bank of India", "exchange": "NSE", "segment": "EQUITY", "base_price": 822.40, "sector": "Banking", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "ITC", "name": "ITC Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 512.60, "sector": "FMCG", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 3740.00, "sector": "Capital Goods", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 982.50, "sector": "Automobile", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 2720.00, "sector": "FMCG", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 7450.00, "sector": "Financial Services", "lot_size": 1, "tick_size": 0.05},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "exchange": "NSE", "segment": "EQUITY", "base_price": 1890.00, "sector": "Healthcare", "lot_size": 1, "tick_size": 0.05},
]


class SimulatedMarketDataProvider(MarketDataProvider):
    """High-fidelity simulated market data provider generating realistic Indian market dynamics."""

    def __init__(self):
        self._connected = False
        self._current_prices: Dict[str, float] = {}
        self._prev_closes: Dict[str, float] = {}
        self._day_opens: Dict[str, float] = {}
        self._day_highs: Dict[str, float] = {}
        self._day_lows: Dict[str, float] = {}
        self._day_volumes: Dict[str, int] = {}
        self._running = False

        for inst in INDIAN_INSTRUMENTS:
            sym = inst["symbol"]
            base = inst["base_price"]
            self._prev_closes[sym] = round(base * (1.0 + random.uniform(-0.015, 0.015)), 2)
            open_price = round(self._prev_closes[sym] * (1.0 + random.uniform(-0.008, 0.008)), 2)
            self._day_opens[sym] = open_price
            self._current_prices[sym] = open_price
            self._day_highs[sym] = open_price
            self._day_lows[sym] = open_price
            self._day_volumes[sym] = random.randint(50000, 500000)

    async def connect(self) -> None:
        self._connected = True
        self._running = True

    async def stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        while self._running:
            # Pick a subset of instruments to simulate tick arrivals
            active_symbols = random.sample([inst["symbol"] for inst in INDIAN_INSTRUMENTS], k=random.randint(3, 7))
            now = datetime.now(timezone.utc)

            for sym in active_symbols:
                old_price = self._current_prices[sym]
                volatility = 0.0008  # ~0.08% micro-move per tick
                drift = random.gauss(0, volatility)
                new_price = round(old_price * (1.0 + drift), 2)
                self._current_prices[sym] = new_price

                # Update extremes
                if new_price > self._day_highs[sym]:
                    self._day_highs[sym] = new_price
                if new_price < self._day_lows[sym]:
                    self._day_lows[sym] = new_price

                qty = random.randint(10, 500)
                self._day_volumes[sym] += qty

                tick = {
                    "symbol": sym,
                    "price": Decimal(str(new_price)),
                    "quantity": qty,
                    "timestamp": now,
                    "source": "simulated",
                    "quality": "HIGH",
                }
                yield tick

            await asyncio.sleep(0.5)

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        sym = symbol.upper()
        if sym not in self._current_prices:
            # Fallback if unknown symbol
            price = 1000.00
            prev_close = 990.00
        else:
            price = self._current_prices[sym]
            prev_close = self._prev_closes[sym]

        change = round(price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

        return {
            "symbol": sym,
            "price": Decimal(str(price)),
            "change": Decimal(str(change)),
            "change_pct": Decimal(str(change_pct)),
            "open": Decimal(str(self._day_opens.get(sym, price))),
            "high": Decimal(str(self._day_highs.get(sym, price))),
            "low": Decimal(str(self._day_lows.get(sym, price))),
            "close": Decimal(str(price)),
            "prev_close": Decimal(str(prev_close)),
            "volume": self._day_volumes.get(sym, 100000),
            "timestamp": datetime.now(timezone.utc),
            "quality": "HIGH"
        }

    async def get_minute_bars(self, symbol: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        sym = symbol.upper()
        current = self._current_prices.get(sym, 1000.00)
        bars = []
        
        # Build 1-minute steps between start and end
        cur_time = start.replace(second=0, microsecond=0)
        end_time = end.replace(second=0, microsecond=0)
        if cur_time > end_time:
            cur_time, end_time = end_time, cur_time

        # Limit to max 500 bars to prevent huge memory
        total_minutes = int((end_time - cur_time).total_seconds() / 60)
        if total_minutes > 500:
            cur_time = end_time - timedelta(minutes=500)

        price = current * (1.0 - (0.0005 * total_minutes))
        while cur_time <= end_time:
            delta = random.gauss(0.0001, 0.002)
            c_open = price
            c_close = round(c_open * (1.0 + delta), 2)
            c_high = round(max(c_open, c_close) * (1.0 + abs(random.gauss(0, 0.001))), 2)
            c_low = round(min(c_open, c_close) * (1.0 - abs(random.gauss(0, 0.001))), 2)
            vol = random.randint(500, 15000)
            price = c_close

            bars.append({
                "interval_start": cur_time,
                "open": Decimal(str(c_open)),
                "high": Decimal(str(c_high)),
                "low": Decimal(str(c_low)),
                "close": Decimal(str(c_close)),
                "volume": vol,
                "source_timestamp": cur_time + timedelta(seconds=59),
                "is_complete": True,
                "quality": "HIGH",
                "source": "simulated"
            })
            cur_time += timedelta(minutes=1)

        return bars

    async def get_historical_data(self, symbol: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        sym = symbol.upper()
        current = self._current_prices.get(sym, 1000.00)
        days = max(1, (end - start).days)
        bars = []

        price = current * (1.0 - (0.002 * min(days, 365)))
        for d in range(min(days, 365)):
            t_date = (start + timedelta(days=d)).replace(hour=15, minute=30, second=0, microsecond=0)
            if t_date.weekday() >= 5:  # skip weekends
                continue
            delta = random.gauss(0.0005, 0.015)
            c_open = round(price, 2)
            c_close = round(c_open * (1.0 + delta), 2)
            c_high = round(max(c_open, c_close) * (1.0 + abs(random.gauss(0, 0.008))), 2)
            c_low = round(min(c_open, c_close) * (1.0 - abs(random.gauss(0, 0.008))), 2)
            vol = random.randint(500000, 5000000)
            price = c_close

            bars.append({
                "trade_date": t_date,
                "open": Decimal(str(c_open)),
                "high": Decimal(str(c_high)),
                "low": Decimal(str(c_low)),
                "close": Decimal(str(c_close)),
                "volume": vol,
                "vwap": Decimal(str(round((c_high + c_low + c_close) / 3, 2)))
            })
        return bars

    async def get_instruments(self) -> List[Dict[str, Any]]:
        return INDIAN_INSTRUMENTS

    async def market_status(self) -> Dict[str, Any]:
        # Calculate status in Indian Standard Time (UTC + 5:30)
        now_utc = datetime.now(timezone.utc)
        ist_offset = timedelta(hours=5, minutes=30)
        now_ist = now_utc + ist_offset
        weekday = now_ist.weekday()  # 0=Monday, 6=Sunday

        if weekday >= 5:
            status = "CLOSED"
            msg = "Exchange closed for weekend"
        else:
            time_val = now_ist.hour * 60 + now_ist.minute
            if 540 <= time_val < 555:  # 09:00 - 09:15
                status = "PRE_OPEN"
                msg = "NSE Pre-market order collection"
            elif 555 <= time_val < 930:  # 09:15 - 15:30
                status = "OPEN"
                msg = "Normal trading session active"
            else:
                status = "CLOSED"
                msg = "Market closed (Normal trading 09:15 - 15:30 IST)"

        return {
            "status": status,
            "exchange": "NSE",
            "trading_day": now_ist.strftime("%Y-%m-%d"),
            "market_time": now_ist,
            "message": msg
        }

    async def close(self) -> None:
        self._running = False
        self._connected = False
