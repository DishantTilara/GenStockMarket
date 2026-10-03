import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.providers.market_data.production_realtime_provider import ProductionRealtimeMarketProvider
from app.providers.market_data.factory import get_market_data_provider, set_market_data_provider
from app.services.market_service import MarketService


@pytest.mark.asyncio
async def test_production_realtime_provider_lifecycle():
    provider = ProductionRealtimeMarketProvider()
    await provider.connect()
    assert provider._connected is True

    health = await provider.health()
    assert health["provider"] == "production_realtime"
    assert health["is_connected"] is True
    assert health["status"] in ["HEALTHY", "STALE", "DISCONNECTED"]
    assert "ingestion_lag_seconds" in health

    status = await provider.market_status()
    assert status["exchange"] == "NSE"
    assert status["status"] in ["OPEN", "PRE_OPEN", "CLOSED"]
    assert "trading_day" in status

    await provider.disconnect()
    assert provider._connected is False


@pytest.mark.asyncio
async def test_production_realtime_provider_quote_and_stale_handling():
    provider = ProductionRealtimeMarketProvider()
    await provider.connect()

    quote = await provider.get_quote("RELIANCE")
    assert quote["symbol"] == "RELIANCE"
    assert quote["exchange"] == "NSE"
    assert float(quote["price"]) > 0
    assert float(quote["bid"]) > 0
    assert float(quote["ask"]) > 0
    assert quote["bid"] <= quote["ask"]
    assert quote["freshness"] in ["FRESH", "STALE"]
    assert "volume" in quote

    # Test stale detection: artificially age timestamp
    provider._cached_quotes["RELIANCE"]["timestamp"] = datetime.now(timezone.utc) - timedelta(seconds=200)
    stale_quote = await provider.get_quote("RELIANCE")
    assert stale_quote["freshness"] == "STALE"

    # Test DATA_UNAVAILABLE fail-closed behavior for nonexistent symbol
    with pytest.raises(LookupError, match="DATA_UNAVAILABLE"):
        await provider.get_quote("COMPLETELY_INVALID_SYMBOL_99999")

    await provider.close()


def test_candle_engine_deterministic_aggregation():
    # Construct sequential 1-minute bars
    base_time = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)
    bars_1m = [
        {
            "symbol": "INFY",
            "interval_start": base_time + timedelta(minutes=0),
            "open": Decimal("1500.00"),
            "high": Decimal("1505.00"),
            "low": Decimal("1498.00"),
            "close": Decimal("1502.00"),
            "volume": 1000
        },
        {
            "symbol": "INFY",
            "interval_start": base_time + timedelta(minutes=1),
            "open": Decimal("1502.00"),
            "high": Decimal("1510.00"),
            "low": Decimal("1501.00"),
            "close": Decimal("1508.00"),
            "volume": 1500
        },
        {
            "symbol": "INFY",
            "interval_start": base_time + timedelta(minutes=2),
            "open": Decimal("1508.00"),
            "high": Decimal("1512.00"),
            "low": Decimal("1506.00"),
            "close": Decimal("1507.00"),
            "volume": 800
        },
        {
            "symbol": "INFY",
            "interval_start": base_time + timedelta(minutes=3),
            "open": Decimal("1507.00"),
            "high": Decimal("1509.00"),
            "low": Decimal("1503.00"),
            "close": Decimal("1504.00"),
            "volume": 1200
        },
        {
            "symbol": "INFY",
            "interval_start": base_time + timedelta(minutes=4),
            "open": Decimal("1504.00"),
            "high": Decimal("1515.00"),
            "low": Decimal("1502.00"),
            "close": Decimal("1514.00"),
            "volume": 2000
        }
    ]

    # Roll up into 5m candle
    candles_5m = ProductionRealtimeMarketProvider.aggregate_bars(bars_1m, "5m")
    assert len(candles_5m) == 1
    c5 = candles_5m[0]
    assert c5["open"] == Decimal("1500.00")
    assert c5["high"] == Decimal("1515.00")  # max of high
    assert c5["low"] == Decimal("1498.00")   # min of low
    assert c5["close"] == Decimal("1514.00") # last close
    assert c5["volume"] == 6500              # sum of volume
    assert c5["timeframe"] == "5m"
    assert c5["is_complete"] is True
    assert c5["quality"] == "HIGH"


@pytest.mark.asyncio
async def test_api_candles_and_market_health(client):
    health_res = await client.get("/health/market-data")
    assert health_res.status_code == 200
    h_data = health_res.json()
    assert "status" in h_data
    assert "provider" in h_data

    candles_res = await client.get("/api/v1/market/candles/RELIANCE?timeframe=5m&limit=10")
    assert candles_res.status_code == 200
    candles = candles_res.json()
    assert isinstance(candles, list)
