from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.providers.market_data.factory import get_market_data_provider
from app.services.market_service import MarketService
from app.schemas.market import InstrumentResponse, QuoteResponse, CandleBarResponse, MarketStatusResponse

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/status", response_model=MarketStatusResponse)
async def get_market_status():
    provider = get_market_data_provider()
    return await provider.market_status()


@router.get("/instruments", response_model=List[InstrumentResponse])
async def get_instruments(db: AsyncSession = Depends(get_db)):
    return await MarketService.ensure_instruments_seeded(db)


@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(symbol: str):
    return await MarketService.get_quote(symbol)


@router.get("/minute/{symbol}", response_model=List[CandleBarResponse])
async def get_minute_bars(
    symbol: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    return await MarketService.get_minute_bars(db, symbol, limit=limit)


@router.get("/history/{symbol}", response_model=List[dict])
async def get_historical_data(
    symbol: str,
    days: int = Query(90, ge=1, le=365)
):
    provider = get_market_data_provider()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    return await provider.get_historical_data(symbol, start, now)
