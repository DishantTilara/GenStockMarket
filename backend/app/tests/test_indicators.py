import pytest
from app.services.indicator_service import IndicatorService


@pytest.mark.asyncio
async def test_indicator_calculations():
    indicators = await IndicatorService.compute_indicators("RELIANCE")
    assert indicators["symbol"] == "RELIANCE"
    assert "current_price" in indicators
    assert "rsi_14" in indicators
    assert 0.0 <= indicators["rsi_14"] <= 100.0
    assert "macd" in indicators
    assert "bollinger_bands" in indicators
    assert "vwap" in indicators
    assert indicators["trend"] in ["BULLISH", "BEARISH", "STRONG_BULLISH", "STRONG_BEARISH", "NEUTRAL"]
