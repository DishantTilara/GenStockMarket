import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.providers.market_data.factory import get_market_data_provider
from app.services.indicator_service import IndicatorService
from app.schemas.scanner import ScanResultItem, ScannerRule

PRESET_SCANNERS = [
    {
        "id": "rsi-oversold",
        "name": "RSI Oversold Bounce",
        "description": "Stocks trading below RSI 35 with price holding above day support",
        "rules": [{"indicator": "RSI", "operator": "<", "value": 35}]
    },
    {
        "id": "ema-bullish-crossover",
        "name": "Golden Trend (EMA 20 > EMA 50)",
        "description": "Bullish momentum where 20 EMA is above 50 EMA and price > VWAP",
        "rules": [
            {"indicator": "EMA_CROSS", "operator": ">", "value": "EMA_50"},
            {"indicator": "PRICE", "operator": ">", "value": "VWAP"}
        ]
    },
    {
        "id": "volume-breakout",
        "name": "Unusual Volume Breakout",
        "description": "Volume at least 1.8x average 20-period volume with positive price gain",
        "rules": [
            {"indicator": "VOLUME_SPIKE", "operator": "==", "value": True},
            {"indicator": "PRICE_CHANGE", "operator": ">", "value": 0.5}
        ]
    },
    {
        "id": "vwap-breakout",
        "name": "VWAP Intraday Surge",
        "description": "Stocks crossing above VWAP with RSI between 50 and 70",
        "rules": [
            {"indicator": "PRICE", "operator": ">", "value": "VWAP"},
            {"indicator": "RSI", "operator": "BETWEEN", "value": [50, 70]}
        ]
    }
]


class ScannerService:
    @staticmethod
    def get_presets() -> List[Dict[str, Any]]:
        return PRESET_SCANNERS

    @classmethod
    async def run_scan(cls, rules: List[Dict[str, Any]]) -> List[ScanResultItem]:
        market_provider = get_market_data_provider()
        instruments = await market_provider.get_instruments()
        results: List[ScanResultItem] = []

        for inst in instruments:
            sym = inst["symbol"]
            quote = await market_provider.get_quote(sym)
            indicators = await IndicatorService.compute_indicators(sym)

            price = float(quote["price"])
            change_pct = float(quote["change_pct"])
            rsi = indicators["rsi_14"]
            vwap = indicators["vwap"]
            ema20 = indicators["ema_20"]
            ema50 = indicators["ema_50"]
            vol_spike = indicators["volume_spike"]

            matched_conditions = []
            matches_all = True

            for rule in rules:
                ind = rule.get("indicator", "").upper()
                op = rule.get("operator", "")
                val = rule.get("value")

                if ind == "RSI":
                    if op == "<" and rsi < float(val):
                        matched_conditions.append(f"RSI {rsi:.1f} < {val}")
                    elif op == ">" and rsi > float(val):
                        matched_conditions.append(f"RSI {rsi:.1f} > {val}")
                    elif op == "BETWEEN" and isinstance(val, list) and len(val) == 2:
                        if val[0] <= rsi <= val[1]:
                            matched_conditions.append(f"RSI {rsi:.1f} between {val[0]} and {val[1]}")
                        else:
                            matches_all = False
                    else:
                        matches_all = False

                elif ind == "PRICE" and val == "VWAP":
                    if op == ">" and price > vwap:
                        matched_conditions.append(f"Price ₹{price:,.2f} > VWAP ₹{vwap:,.2f}")
                    elif op == "<" and price < vwap:
                        matched_conditions.append(f"Price ₹{price:,.2f} < VWAP ₹{vwap:,.2f}")
                    else:
                        matches_all = False

                elif ind in ["EMA_CROSS", "EMA"]:
                    if str(val).upper() == "EMA_50":
                        if ema20 > ema50:
                            matched_conditions.append(f"EMA 20 (₹{ema20:,.2f}) > EMA 50 (₹{ema50:,.2f})")
                        else:
                            matches_all = False

                elif ind == "VOLUME_SPIKE":
                    if vol_spike:
                        matched_conditions.append("Volume > 1.8x 20-period avg")
                    else:
                        matches_all = False

                elif ind == "PRICE_CHANGE":
                    if change_pct > float(val):
                        matched_conditions.append(f"Change {change_pct:+.2f}% > {val}%")
                    else:
                        matches_all = False

            if matches_all and matched_conditions:
                results.append(ScanResultItem(
                    symbol=sym,
                    name=inst["name"],
                    price=quote["price"],
                    change_pct=quote["change_pct"],
                    volume=quote["volume"],
                    matched_conditions=matched_conditions,
                    metrics={
                        "rsi": rsi,
                        "vwap": vwap,
                        "ema_20": ema20,
                        "ema_50": ema50,
                        "volume_spike": vol_spike
                    }
                ))

        return results

    @classmethod
    async def translate_natural_language_query(cls, query: str) -> Dict[str, Any]:
        """Convert natural language market scan query into structured JSON scanner rules."""
        rules = []
        name = "Custom Scanner"
        description = query

        q_lower = query.lower()

        # Check EMA 20
        if "20 ema" in q_lower or "ema 20" in q_lower:
            rules.append({"indicator": "PRICE", "operator": ">", "value": "EMA_20"})
        elif "ema" in q_lower and "50" in q_lower:
            rules.append({"indicator": "EMA_CROSS", "operator": ">", "value": "EMA_50"})

        # Check RSI range or levels
        rsi_match = re.search(r"rsi\s*(?:between\s*(\d+)\s*(?:and|-)\s*(\d+)|([<>]=?)\s*(\d+))", q_lower)
        if rsi_match:
            if rsi_match.group(1) and rsi_match.group(2):
                low_r, high_r = float(rsi_match.group(1)), float(rsi_match.group(2))
                rules.append({"indicator": "RSI", "operator": "BETWEEN", "value": [low_r, high_r]})
            elif rsi_match.group(3) and rsi_match.group(4):
                rules.append({"indicator": "RSI", "operator": rsi_match.group(3), "value": float(rsi_match.group(4))})
        else:
            if "rsi" in q_lower and ("50" in q_lower or "70" in q_lower):
                rules.append({"indicator": "RSI", "operator": "BETWEEN", "value": [50.0, 70.0]})

        # Check Volume
        if "volume" in q_lower and ("2x" in q_lower or "spike" in q_lower or "unusual" in q_lower or "breakout" in q_lower):
            rules.append({"indicator": "VOLUME_SPIKE", "operator": "==", "value": True})

        # Check VWAP
        if "vwap" in q_lower:
            rules.append({"indicator": "PRICE", "operator": ">", "value": "VWAP"})

        if not rules:
            # Default fallback rule if query was broad
            rules.append({"indicator": "RSI", "operator": "<", "value": 45.0})

        return {
            "name": name,
            "description": description,
            "rules": rules
        }
