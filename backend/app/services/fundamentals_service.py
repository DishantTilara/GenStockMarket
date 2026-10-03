import asyncio
import json
import logging
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.core.redis import redis_service
from app.providers.market_data.symbol_mapper import IndianSymbolMapper

logger = logging.getLogger(__name__)

# Fallback in-memory cache in case Redis is disabled or offline
_MEMORY_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour


def safe_float(val: Any) -> Optional[float]:
    """Helper to convert values to float while strictly preserving None/NaN as None."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _df_to_statement_rows(df: Any, max_rows: int = 15, max_cols: int = 4) -> List[Dict[str, Any]]:
    """Convert pandas DataFrame (yfinance financial statement) to API serializable rows."""
    if df is None or not hasattr(df, "index") or not hasattr(df, "columns"):
        return []
    try:
        rows = []
        cols = [str(c)[:10] for c in list(df.columns)[:max_cols]]
        for idx in list(df.index)[:max_rows]:
            val_map = {}
            for col_idx, col_name in enumerate(list(df.columns)[:max_cols]):
                val = df.loc[idx, col_name] if col_name in df.columns else None
                val_map[cols[col_idx]] = safe_float(val)
            rows.append({"metric": str(idx), "values": val_map})
        return rows
    except Exception as exc:
        logger.warning(f"Error converting financial statement dataframe: {exc}")
        return []


def _fetch_yfinance_fundamentals_sync(provider_symbol: str, raw_symbol: str) -> Dict[str, Any]:
    """Synchronous yfinance extraction to run in thread pool."""
    import yfinance as yf

    ticker = yf.Ticker(provider_symbol)
    info = ticker.info or {}

    income_stmt = _df_to_statement_rows(getattr(ticker, "financials", None))
    balance_sheet = _df_to_statement_rows(getattr(ticker, "balance_sheet", None))
    cashflow = _df_to_statement_rows(getattr(ticker, "cashflow", None))

    return {
        "symbol": raw_symbol.upper(),
        "company_name": info.get("longName") or info.get("shortName") or raw_symbol.upper(),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency") or "INR",
        "market_cap": safe_float(info.get("marketCap")),
        "pe_ratio": safe_float(info.get("trailingPE")),
        "forward_pe": safe_float(info.get("forwardPE")),
        "peg_ratio": safe_float(info.get("pegRatio")),
        "eps": safe_float(info.get("trailingEps")),
        "book_value": safe_float(info.get("bookValue")),
        "pb_ratio": safe_float(info.get("priceToBook")),
        "dividend_yield": safe_float(info.get("dividendYield")),
        "dividend_rate": safe_float(info.get("dividendRate")),
        "total_debt": safe_float(info.get("totalDebt")),
        "debt_to_equity": safe_float(info.get("debtToEquity")),
        "total_revenue": safe_float(info.get("totalRevenue")),
        "net_income": safe_float(info.get("netIncomeToCommon")),
        "operating_cash_flow": safe_float(info.get("operatingCashflow")),
        "free_cash_flow": safe_float(info.get("freeCashflow")),
        "roe": safe_float(info.get("returnOnEquity")),
        "roa": safe_float(info.get("returnOnAssets")),
        "profit_margin": safe_float(info.get("profitMargins")),
        "operating_margin": safe_float(info.get("operatingMargins")),
        "income_statement": income_stmt,
        "balance_sheet": balance_sheet,
        "cashflow_statement": cashflow,
        "provider": "yfinance",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _get_simulated_fundamentals(symbol: str) -> Dict[str, Any]:
    """Realistic fallback fundamentals for offline/mock development and testing."""
    sym = symbol.upper()
    sim_data: Dict[str, Dict[str, Any]] = {
        "RELIANCE": {
            "company_name": "Reliance Industries Limited",
            "sector": "Energy & Conglomerate",
            "industry": "Oil, Gas & Telecom",
            "market_cap": 16250000000000.0,
            "pe_ratio": 24.5,
            "forward_pe": 21.8,
            "eps": 105.4,
            "book_value": 1150.2,
            "pb_ratio": 2.2,
            "dividend_yield": 0.0038,
            "dividend_rate": 10.0,
            "total_debt": 3120000000000.0,
            "debt_to_equity": 0.41,
            "total_revenue": 9000000000000.0,
            "net_income": 690000000000.0,
            "operating_cash_flow": 1250000000000.0,
            "free_cash_flow": 450000000000.0,
            "roe": 0.095,
            "roa": 0.052,
            "profit_margin": 0.076,
            "operating_margin": 0.124,
        },
        "TCS": {
            "company_name": "Tata Consultancy Services Limited",
            "sector": "Technology",
            "industry": "IT Services & Consulting",
            "market_cap": 14500000000000.0,
            "pe_ratio": 29.2,
            "forward_pe": 26.0,
            "eps": 132.8,
            "book_value": 265.4,
            "pb_ratio": 14.5,
            "dividend_yield": 0.0135,
            "dividend_rate": 52.0,
            "total_debt": 78000000000.0,
            "debt_to_equity": 0.08,
            "total_revenue": 2400000000000.0,
            "net_income": 460000000000.0,
            "operating_cash_flow": 480000000000.0,
            "free_cash_flow": 440000000000.0,
            "roe": 0.495,
            "roa": 0.312,
            "profit_margin": 0.192,
            "operating_margin": 0.248,
        },
        "INFY": {
            "company_name": "Infosys Limited",
            "sector": "Technology",
            "industry": "IT Services & Consulting",
            "market_cap": 7500000000000.0,
            "pe_ratio": 27.5,
            "forward_pe": 24.2,
            "eps": 65.2,
            "book_value": 210.0,
            "pb_ratio": 8.5,
            "dividend_yield": 0.021,
            "dividend_rate": 38.0,
            "total_debt": 92000000000.0,
            "debt_to_equity": 0.11,
            "total_revenue": 1550000000000.0,
            "net_income": 265000000000.0,
            "operating_cash_flow": 270000000000.0,
            "free_cash_flow": 240000000000.0,
            "roe": 0.315,
            "roa": 0.210,
            "profit_margin": 0.171,
            "operating_margin": 0.212,
        },
        "HDFCBANK": {
            "company_name": "HDFC Bank Limited",
            "sector": "Financial Services",
            "industry": "Private Sector Banking",
            "market_cap": 12800000000000.0,
            "pe_ratio": 19.4,
            "forward_pe": 17.1,
            "eps": 88.5,
            "book_value": 560.0,
            "pb_ratio": 2.9,
            "dividend_yield": 0.011,
            "dividend_rate": 19.5,
            "total_debt": None,
            "debt_to_equity": None,
            "total_revenue": 2150000000000.0,
            "net_income": 640000000000.0,
            "operating_cash_flow": None,
            "free_cash_flow": None,
            "roe": 0.165,
            "roa": 0.019,
            "profit_margin": 0.298,
            "operating_margin": 0.385,
        },
    }

    base = sim_data.get(
        sym,
        {
            "company_name": f"{sym} Limited",
            "sector": "General Industry",
            "industry": "Commercial & Industrial",
            "market_cap": 500000000000.0,
            "pe_ratio": 22.0,
            "forward_pe": 19.5,
            "eps": 45.0,
            "book_value": 320.0,
            "pb_ratio": 3.1,
            "dividend_yield": 0.012,
            "dividend_rate": 12.0,
            "total_debt": 150000000000.0,
            "debt_to_equity": 0.45,
            "total_revenue": 850000000000.0,
            "net_income": 95000000000.0,
            "operating_cash_flow": 110000000000.0,
            "free_cash_flow": 75000000000.0,
            "roe": 0.145,
            "roa": 0.082,
            "profit_margin": 0.112,
            "operating_margin": 0.165,
        },
    )

    sample_income_stmt = [
        {"metric": "Total Revenue", "values": {"2024": base["total_revenue"], "2023": base["total_revenue"] * 0.9}},
        {"metric": "Operating Income", "values": {"2024": base["total_revenue"] * base["operating_margin"], "2023": (base["total_revenue"] * 0.9) * (base["operating_margin"] * 0.95)}},
        {"metric": "Net Income", "values": {"2024": base["net_income"], "2023": base["net_income"] * 0.88}},
    ]

    return {
        "symbol": sym,
        **base,
        "currency": "INR",
        "income_statement": sample_income_stmt,
        "balance_sheet": [],
        "cashflow_statement": [],
        "provider": "simulated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class FundamentalsService:
    """Service to fetch, normalize, and cache fundamental financial data."""

    @classmethod
    async def get_fundamentals(cls, symbol: str) -> Dict[str, Any]:
        """
        Retrieve fundamental metrics and statements for an Indian equity.
        Uses Redis cache with memory fallback.
        """
        clean_symbol = symbol.strip().upper()
        cache_key = f"market:fundamentals:{clean_symbol}"

        # 1. Try Redis cache
        try:
            cached = await redis_service.get(cache_key)
            if cached:
                if isinstance(cached, str):
                    return json.loads(cached)
                return cached
        except Exception:
            pass

        # 2. Check memory cache
        if clean_symbol in _MEMORY_CACHE:
            entry = _MEMORY_CACHE[clean_symbol]
            return entry

        # 3. Provider Resolution
        provider_name = getattr(settings, "MARKET_DATA_PROVIDER", "yfinance").lower()
        provider_symbol = IndianSymbolMapper.to_provider_symbol(clean_symbol)

        data = None
        if provider_name == "yfinance":
            try:
                data = await asyncio.to_thread(_fetch_yfinance_fundamentals_sync, provider_symbol, clean_symbol)
            except Exception as exc:
                logger.warning(f"yfinance failed to fetch fundamentals for {clean_symbol} ({provider_symbol}): {exc}")

        # If data is empty or missing, fallback to simulated profile
        if not data or not data.get("company_name"):
            data = _get_simulated_fundamentals(clean_symbol)

        # 4. Cache data
        try:
            await redis_service.set(cache_key, json.dumps(data, default=str), ttl=_CACHE_TTL_SECONDS)
        except Exception:
            pass

        _MEMORY_CACHE[clean_symbol] = data
        return data
