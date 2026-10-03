from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.providers.market_data.factory import get_market_data_provider
from app.services.market_service import MarketService
from app.schemas.market import (
    InstrumentResponse,
    InstrumentSearchResponse,
    QuoteResponse,
    CandleBarResponse,
    MarketStatusResponse,
    FundamentalsResponse,
)
from app.schemas.options import OptionChainResponse
from app.services.fundamentals_service import FundamentalsService
from app.services.options_service import OptionsService

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/status", response_model=MarketStatusResponse)
async def get_market_status():
    """Retrieve Indian market session status (OPEN, PRE_OPEN, CLOSED)."""
    provider = get_market_data_provider()
    return await provider.market_status()


@router.get("/instruments", response_model=List[InstrumentResponse])
async def get_instruments(db: AsyncSession = Depends(get_db)):
    """Retrieve all active Indian equities and indices."""
    return await MarketService.ensure_instruments_seeded(db)


@router.get("/search", response_model=List[InstrumentSearchResponse])
async def search_instruments(
    q: str = Query("", description="Symbol or company name prefix/substring"),
    db: AsyncSession = Depends(get_db)
):
    """Search Indian equities and indices by symbol or name."""
    return await MarketService.search_instruments(db, q)


@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(symbol: str):
    """Retrieve latest validated quote with freshness indicator."""
    return await MarketService.get_quote(symbol)


@router.get("/minute/{symbol}", response_model=List[CandleBarResponse])
async def get_minute_bars(
    symbol: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve 1-minute historical candlestick bars."""
    return await MarketService.get_minute_bars(db, symbol, limit=limit)


@router.get("/candles/{symbol}", response_model=List[CandleBarResponse])
async def get_candles(
    symbol: str,
    timeframe: str = Query("1m", pattern="^(1m|5m|15m|30m|1h|1H|1d|1D)$"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve historical candlestick bars across supported timeframes."""
    return await MarketService.get_candles(db, symbol, timeframe=timeframe, limit=limit)


@router.get("/history/{symbol}", response_model=List[dict])
async def get_historical_data(
    symbol: str,
    days: int = Query(90, ge=1, le=365)
):
    """Retrieve daily historical trading bars."""
    provider = get_market_data_provider()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    return await provider.get_historical_data(symbol, start, now)


@router.get("/fundamentals/{symbol}", response_model=FundamentalsResponse)
async def get_fundamentals(symbol: str):
    """
    Retrieve comprehensive company fundamentals (P/E, Market Cap, EPS, Financials, Debt, Cash Flow).
    Missing values are returned as None (rendered as N/A). Never reported as zero.
    """
    return await FundamentalsService.get_fundamentals(symbol)


@router.get("/options/{symbol}", response_model=OptionChainResponse)
async def get_option_chain(
    symbol: str,
    expiry: Optional[str] = Query(None, description="Expiration date in YYYY-MM-DD format"),
):
    """
    Retrieve live/computed Indian equity and index Option Chain.
    Includes Calls, Puts, Strikes, Bid/Ask, OI, IV, PCR Ratio, and Max Pain.
    For Paper Trading and Market Analysis only.
    """
    return await OptionsService.get_option_chain(symbol, expiry=expiry)


