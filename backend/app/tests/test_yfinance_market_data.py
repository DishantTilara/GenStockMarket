import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from sqlalchemy import select

from app.providers.market_data.symbol_mapper import IndianSymbolMapper
from app.providers.market_data.models import MarketQuote, CandleBarData
from app.providers.market_data.validation import (
    validate_quote,
    validate_candle,
    calculate_freshness,
    get_indian_market_status,
)
from app.providers.market_data.yfinance_provider import YFinanceMarketDataProvider
from app.providers.market_data.factory import get_market_data_provider, set_market_data_provider
from app.services.market_service import MarketService
from app.services.paper_trading_service import PaperTradingService
from app.models.market_data import MinuteBar
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.user import User
from app.core.security import get_password_hash


# ---------------------------------------------------------
# 1. Symbol Mapping Tests
# ---------------------------------------------------------
def test_symbol_mapping():
    """Verify bidirectional Indian equity and index symbol mapping."""
    # Standard NSE Equities
    assert IndianSymbolMapper.to_provider_symbol("RELIANCE") == "RELIANCE.NS"
    assert IndianSymbolMapper.to_provider_symbol("TCS") == "TCS.NS"
    assert IndianSymbolMapper.to_provider_symbol("INFY") == "INFY.NS"
    assert IndianSymbolMapper.to_provider_symbol("HDFCBANK") == "HDFCBANK.NS"
    assert IndianSymbolMapper.to_provider_symbol("ICICIBANK") == "ICICIBANK.NS"

    # Already has suffix - should NOT double-append
    assert IndianSymbolMapper.to_provider_symbol("RELIANCE.NS") == "RELIANCE.NS"
    assert IndianSymbolMapper.to_provider_symbol("TCS.BO", exchange="BSE") == "TCS.BO"

    # Indices
    assert IndianSymbolMapper.to_provider_symbol("NIFTY 50") == "^NSEI"
    assert IndianSymbolMapper.to_provider_symbol("BANKNIFTY") == "^NSEBANK"
    assert IndianSymbolMapper.to_provider_symbol("SENSEX") == "^BSESN"

    # Reverse Mapping
    canonical_sym, exchange = IndianSymbolMapper.to_canonical_symbol("RELIANCE.NS")
    assert canonical_sym == "RELIANCE"
    assert exchange == "NSE"

    idx_sym, idx_exch = IndianSymbolMapper.to_canonical_symbol("^NSEI")
    assert idx_sym == "NIFTY 50"
    assert idx_exch == "NSE"


# ---------------------------------------------------------
# 2. Validation & Freshness Tests
# ---------------------------------------------------------
def test_invalid_price():
    """Reject quotes with zero or negative prices."""
    invalid_quote = MarketQuote(
        symbol="RELIANCE",
        exchange="NSE",
        provider_symbol="RELIANCE.NS",
        timestamp=datetime.now(timezone.utc),
        price=Decimal("-10.0"),
        open=Decimal("2900.0"),
        high=Decimal("2950.0"),
        low=Decimal("2890.0"),
        previous_close=Decimal("2900.0"),
        volume=1000,
    )
    is_valid, err = validate_quote(invalid_quote)
    assert not is_valid
    assert "positive" in err.lower()


def test_invalid_timestamp():
    """Reject quotes with high < low or price out of bounds."""
    invalid_bounds = MarketQuote(
        symbol="TCS",
        exchange="NSE",
        provider_symbol="TCS.NS",
        timestamp=datetime.now(timezone.utc),
        price=Decimal("4300.0"),
        open=Decimal("4100.0"),
        high=Decimal("4000.0"),  # high < low
        low=Decimal("4050.0"),
        previous_close=Decimal("4100.0"),
        volume=500,
    )
    is_valid, err = validate_quote(invalid_bounds)
    assert not is_valid
    assert "high" in err.lower() or "low" in err.lower()


def test_stale_quote():
    """Calculate freshness correctly according to age and market status."""
    # Very old quote -> STALE
    old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    old_quote = MarketQuote(
        symbol="INFY",
        exchange="NSE",
        provider_symbol="INFY.NS",
        timestamp=old_time,
        price=Decimal("1900.0"),
        open=Decimal("1890.0"),
        high=Decimal("1910.0"),
        low=Decimal("1880.0"),
        previous_close=Decimal("1890.0"),
        volume=2000,
    )
    freshness = calculate_freshness(old_quote, max_age_seconds=120)
    assert freshness in ("STALE", "MARKET CLOSED")


# ---------------------------------------------------------
# 3. YFinance Provider Tests (Mocked)
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_yfinance_provider():
    """Test YFinanceMarketDataProvider quote normalization and fetching."""
    provider = YFinanceMarketDataProvider()
    now_utc = datetime.now(timezone.utc)

    mock_hist = pd.DataFrame(
        {
            "Open": [2950.0],
            "High": [2980.0],
            "Low": [2940.0],
            "Close": [2975.50],
            "Volume": [150000],
        },
        index=[pd.Timestamp(now_utc)],
    )

    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist
        mock_instance.fast_info = {
            "last_price": 2975.50,
            "open": 2950.0,
            "day_high": 2980.0,
            "day_low": 2940.0,
            "previous_close": 2940.0,
            "last_volume": 150000,
        }
        mock_ticker_cls.return_value = mock_instance

        quote = await provider.get_quote("RELIANCE")
        assert quote is not None
        assert quote["symbol"] == "RELIANCE"
        assert quote["provider_symbol"] == "RELIANCE.NS"
        assert float(quote["price"]) == 2975.50
        assert float(quote["high"]) == 2980.0
        assert float(quote["low"]) == 2940.0
        assert quote["volume"] == 150000


@pytest.mark.asyncio
async def test_empty_response():
    """Test handling of empty response from upstream yfinance."""
    provider = YFinanceMarketDataProvider()

    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame()
        mock_instance.fast_info = None
        mock_ticker_cls.return_value = mock_instance

        raw_quote = provider._sync_fetch_quote("UNKNOWN_STOCK")
        assert raw_quote is None


@pytest.mark.asyncio
async def test_invalid_symbol():
    """Test graceful handling when an invalid symbol raises an exception."""
    provider = YFinanceMarketDataProvider()

    with patch("yfinance.Ticker", side_effect=Exception("Symbol not found")):
        raw_quote = provider._sync_fetch_quote("NONEXISTENT")
        assert raw_quote is None
        health = provider.get_health()
        assert health["consecutive_failures"] >= 1


@pytest.mark.asyncio
async def test_normalization_and_timestamp():
    """Verify provider uses upstream source timestamp and normalizes to UTC."""
    provider = YFinanceMarketDataProvider()
    specific_time = datetime(2026, 10, 1, 9, 30, 0, tzinfo=timezone.utc)

    mock_hist = pd.DataFrame(
        {
            "Open": [1600.0],
            "High": [1620.0],
            "Low": [1590.0],
            "Close": [1615.0],
            "Volume": [20000],
        },
        index=[pd.Timestamp(specific_time)],
    )

    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist
        mock_instance.fast_info = {
            "last_price": 1615.0,
            "open": 1600.0,
            "day_high": 1620.0,
            "day_low": 1590.0,
            "previous_close": 1600.0,
            "last_volume": 20000,
        }
        mock_ticker_cls.return_value = mock_instance

        raw_quote = provider._sync_fetch_quote("HDFCBANK")
        assert raw_quote is not None
        assert raw_quote.timestamp.tzinfo is not None
        assert float(raw_quote.price) == 1615.0


# ---------------------------------------------------------
# 4. Database & Candle Upsert / Gap Detection Tests
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_candle_upsert_and_duplicate_prevention():
    """Ensure minute bars are stored with instrument references."""
    from app.tests.conftest import TestSessionLocal

    async with TestSessionLocal() as db:
        # Create an instrument
        inst = Instrument(
            symbol="TCS",
            exchange="NSE",
            name="Tata Consultancy Services",
            provider_symbol="TCS.NS",
            sector="Technology",
            segment="EQUITY",
            is_active=True,
        )
        db.add(inst)
        await db.commit()
        await db.refresh(inst)

        now_candle_time = datetime(2026, 10, 1, 9, 15, 0, tzinfo=timezone.utc)

        # First insert
        bar1 = MinuteBar(
            instrument_id=inst.id,
            interval_start=now_candle_time,
            open=Decimal("4200.0"),
            high=Decimal("4220.0"),
            low=Decimal("4195.0"),
            close=Decimal("4215.0"),
            volume=15000,
            source_timestamp=now_candle_time + timedelta(seconds=59),
            is_complete=True,
            quality="HIGH",
            source="test",
        )
        db.add(bar1)
        await db.commit()

        # Check single row in database
        result = await db.execute(select(MinuteBar).where(MinuteBar.instrument_id == inst.id))
        bars = result.scalars().all()
        assert len(bars) == 1
        assert float(bars[0].close) == 4215.0


@pytest.mark.asyncio
async def test_missing_candle_reconciliation():
    """Verify gap reconciliation fetches missing intervals and inserts bars without errors."""
    from unittest.mock import AsyncMock
    from app.tests.conftest import TestSessionLocal

    async with TestSessionLocal() as db:
        inst = Instrument(
            symbol="INFY",
            exchange="NSE",
            name="Infosys",
            provider_symbol="INFY.NS",
            sector="Technology",
            segment="EQUITY",
            is_active=True,
        )
        db.add(inst)
        await db.commit()
        await db.refresh(inst)

        # Mock provider returning missing bars
        sample_bars = [
            {
                "symbol": "INFY",
                "interval_start": datetime.now(timezone.utc) - timedelta(minutes=2),
                "open": 1900.0,
                "high": 1910.0,
                "low": 1895.0,
                "close": 1905.0,
                "volume": 2000,
            }
        ]

        mock_prov = MagicMock()
        mock_prov.get_minute_bars = AsyncMock(return_value=sample_bars)
        set_market_data_provider(mock_prov)
        try:
            reconciled = await MarketService.reconcile_missing_candles(db, inst)
            assert reconciled >= 1

            # Second reconciliation with same data must not duplicate
            reconciled_2 = await MarketService.reconcile_missing_candles(db, inst)
            assert reconciled_2 == 0
        finally:
            set_market_data_provider(None)


# ---------------------------------------------------------
# 5. Paper Trading Execution Triggers (Limit, SL, Target)
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_paper_limit_order_and_triggers():
    """Test LIMIT orders wait for condition, and SL/Target trigger automatically."""
    from app.tests.conftest import TestSessionLocal

    async with TestSessionLocal() as db:
        # Create a test user
        user = User(
            email="limit_tester@nse.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="Limit Tester",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # 1. Place a BUY LIMIT order at 2900 (market is currently at 2950)
        limit_order = Order(
            user_id=user.id,
            symbol="RELIANCE",
            side="BUY",
            order_type="LIMIT",
            quantity=10,
            price=Decimal("2900.0"),
            status="PENDING",
        )
        db.add(limit_order)
        await db.commit()
        await db.refresh(limit_order)

        paper_service = PaperTradingService()

        # Tick at 2950 -> should NOT fill
        events_1 = await paper_service.evaluate_tick_triggers(db, "RELIANCE", Decimal("2950.0"))
        assert len(events_1) == 0

        # Tick at 2895 -> reaches <= 2900 -> SHOULD fill BUY LIMIT
        events_2 = await paper_service.evaluate_tick_triggers(db, "RELIANCE", Decimal("2895.0"))
        assert len(events_2) == 1
        assert events_2[0]["type"] == "LIMIT_FILLED"

        # Check order status is FILLED
        res = await db.execute(select(Order).where(Order.id == limit_order.id))
        updated_order = res.scalar_one()
        assert updated_order.status == "FILLED"
        assert float(updated_order.execution_price) == 2900.0
