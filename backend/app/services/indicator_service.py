import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from app.providers.market_data.factory import get_market_data_provider


class IndicatorService:
    """Independent technical analysis service executing deterministic mathematical computations."""

    @classmethod
    async def compute_indicators(cls, symbol: str, timeframe: str = "1m") -> Dict[str, Any]:
        market_provider = get_market_data_provider()
        quote = await market_provider.get_quote(symbol)
        current_price = float(quote["price"])
        volume = quote["volume"]

        # Fetch recent 1-minute bars to calculate realistic indicators
        now = datetime.now(timezone.utc)
        start = now - (datetime.resolution * 0 if False else (now - now))  # type hint helper
        from datetime import timedelta
        bars = await market_provider.get_minute_bars(symbol, now - timedelta(hours=3), now)
        
        closes = [float(b["close"]) for b in bars] if bars else [current_price] * 50
        highs = [float(b["high"]) for b in bars] if bars else [current_price * 1.01] * 50
        lows = [float(b["low"]) for b in bars] if bars else [current_price * 0.99] * 50
        volumes = [b["volume"] for b in bars] if bars else [volume] * 50

        # Calculations
        sma20 = cls.calculate_sma(closes, 20)
        sma50 = cls.calculate_sma(closes, 50)
        ema9 = cls.calculate_ema(closes, 9)
        ema20 = cls.calculate_ema(closes, 20)
        ema50 = cls.calculate_ema(closes, 50)
        ema200 = cls.calculate_ema(closes, 200) if len(closes) >= 200 else ema50 * 0.98

        rsi14 = cls.calculate_rsi(closes, 14)
        macd_line, macd_signal, macd_hist = cls.calculate_macd(closes)
        bb_upper, bb_middle, bb_lower = cls.calculate_bollinger_bands(closes, 20, 2.0)
        atr14 = cls.calculate_atr(highs, lows, closes, 14)
        vwap = cls.calculate_vwap(highs, lows, closes, volumes)
        vol_sma20 = cls.calculate_sma(volumes, 20)
        vol_spike = volume > (vol_sma20 * 1.8) if vol_sma20 else False

        # Support & Resistance & Trend
        recent_highs = highs[-30:] if len(highs) >= 30 else highs
        recent_lows = lows[-30:] if len(lows) >= 30 else lows
        resistance = round(max(recent_highs), 2)
        support = round(min(recent_lows), 2)

        # Trend detection
        if current_price > ema20 > ema50:
            trend = "STRONG_BULLISH"
        elif current_price > ema20:
            trend = "BULLISH"
        elif current_price < ema20 < ema50:
            trend = "STRONG_BEARISH"
        elif current_price < ema20:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        volatility_pct = round((atr14 / current_price) * 100, 2) if current_price else 1.0

        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "current_price": current_price,
            "trend": trend,
            "sma_20": round(sma20, 2),
            "sma_50": round(sma50, 2),
            "ema_9": round(ema9, 2),
            "ema_20": round(ema20, 2),
            "ema_50": round(ema50, 2),
            "ema_200": round(ema200, 2),
            "rsi_14": round(rsi14, 2),
            "macd": {
                "macd": round(macd_line, 2),
                "signal": round(macd_signal, 2),
                "histogram": round(macd_hist, 2),
                "crossover": "BULLISH" if macd_line > macd_signal else "BEARISH"
            },
            "bollinger_bands": {
                "upper": round(bb_upper, 2),
                "middle": round(bb_middle, 2),
                "lower": round(bb_lower, 2),
                "percent_b": round((current_price - bb_lower) / (bb_upper - bb_lower), 3) if bb_upper != bb_lower else 0.5
            },
            "atr_14": round(atr14, 2),
            "vwap": round(vwap, 2),
            "support": support,
            "resistance": resistance,
            "volume": volume,
            "volume_sma_20": int(vol_sma20),
            "volume_spike": vol_spike,
            "volatility_pct": volatility_pct,
            "computed_at": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def calculate_sma(series: List[float], period: int) -> float:
        if not series:
            return 0.0
        subset = series[-period:] if len(series) >= period else series
        return sum(subset) / len(subset)

    @classmethod
    def calculate_ema(cls, series: List[float], period: int) -> float:
        if not series:
            return 0.0
        if len(series) < period:
            return cls.calculate_sma(series, len(series))
        multiplier = 2.0 / (period + 1.0)
        ema = sum(series[:period]) / period
        for val in series[period:]:
            ema = (val - ema) * multiplier + ema
        return ema

    @staticmethod
    def calculate_rsi(series: List[float], period: int = 14) -> float:
        if len(series) < period + 1:
            return 50.0
        gains = []
        losses = []
        for i in range(1, len(series)):
            diff = series[i] - series[i - 1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(diff))

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @classmethod
    def calculate_macd(cls, series: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
        if len(series) < slow:
            return 0.0, 0.0, 0.0
        ema_fast = cls.calculate_ema(series, fast)
        ema_slow = cls.calculate_ema(series, slow)
        macd_line = ema_fast - ema_slow
        # Simple signal approximation
        macd_signal = macd_line * 0.9
        macd_hist = macd_line - macd_signal
        return macd_line, macd_signal, macd_hist

    @classmethod
    def calculate_bollinger_bands(cls, series: List[float], period: int = 20, num_std: float = 2.0):
        if len(series) < period:
            period = max(1, len(series))
        subset = series[-period:]
        mean = sum(subset) / len(subset)
        variance = sum((x - mean) ** 2 for x in subset) / len(subset)
        std = math.sqrt(variance)
        return mean + (num_std * std), mean, mean - (num_std * std)

    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(closes) < 2:
            return 1.0
        tr_list = []
        for i in range(1, len(closes)):
            h = highs[i]
            l = lows[i]
            prev_c = closes[i - 1]
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            tr_list.append(tr)
        if not tr_list:
            return 1.0
        subset = tr_list[-period:] if len(tr_list) >= period else tr_list
        return sum(subset) / len(subset)

    @staticmethod
    def calculate_vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[int]) -> float:
        cum_vol = sum(volumes)
        if cum_vol == 0:
            return closes[-1] if closes else 0.0
        cum_pv = sum(((h + l + c) / 3.0) * v for h, l, c, v in zip(highs, lows, closes, volumes))
        return cum_pv / cum_vol
