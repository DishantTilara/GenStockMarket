from fastapi import APIRouter, Query
from app.services.indicator_service import IndicatorService

router = APIRouter(prefix="/technical", tags=["Technical Indicators"])


@router.get("/{symbol}")
async def get_technical_indicators(
    symbol: str,
    timeframe: str = Query("1m", pattern="^(1m|5m|15m|1d)$")
):
    return await IndicatorService.compute_indicators(symbol, timeframe)
