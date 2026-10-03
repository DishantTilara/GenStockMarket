import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.fundamentals_service import FundamentalsService, safe_float


def test_safe_float_helper():
    assert safe_float(12.34) == 12.34
    assert safe_float(None) is None
    assert safe_float("invalid") is None
    assert safe_float(float("nan")) is None
    assert safe_float(float("inf")) is None
    assert safe_float(0.0) == 0.0


@pytest.mark.asyncio
async def test_fundamentals_service_simulated_fallback():
    # Test service returns valid fundamental structure for standard Indian symbol
    data = await FundamentalsService.get_fundamentals("RELIANCE")
    assert data["symbol"] == "RELIANCE"
    assert "Reliance" in data["company_name"]
    assert data["market_cap"] is not None
    assert data["market_cap"] > 0
    assert data["pe_ratio"] is not None
    assert "income_statement" in data


@pytest.mark.asyncio
async def test_fundamentals_missing_values_remain_none():
    from app.services.fundamentals_service import _MEMORY_CACHE
    _MEMORY_CACHE.clear()
    # Test that unknown or missing fields are None and not converted to 0
    with patch("app.core.config.settings.MARKET_DATA_PROVIDER", "yfinance"):
        with patch("app.services.fundamentals_service._fetch_yfinance_fundamentals_sync") as mock_yf:
            mock_yf.return_value = {
                "symbol": "UNKNOWNCO",
                "company_name": "Unknown Co Ltd",
                "sector": None,
                "industry": None,
                "currency": "INR",
                "market_cap": None,
                "pe_ratio": None,
                "eps": None,
                "book_value": None,
                "total_debt": None,
                "income_statement": [],
                "balance_sheet": [],
                "cashflow_statement": [],
                "provider": "yfinance",
                "timestamp": "2026-10-01T00:00:00Z",
            }
            res = await FundamentalsService.get_fundamentals("UNKNOWNCO")
            assert res["market_cap"] is None
            assert res["pe_ratio"] is None
            assert res["eps"] is None
            # Must strictly NOT be 0
            assert res["market_cap"] != 0
            assert res["pe_ratio"] != 0


@pytest.mark.asyncio
async def test_fundamentals_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/market/fundamentals/TCS")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol"] == "TCS"
        assert body["company_name"] is not None
        assert "income_statement" in body
