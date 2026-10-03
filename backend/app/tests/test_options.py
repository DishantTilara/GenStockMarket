import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.options_service import (
    OptionsService,
    _black_scholes,
    _get_strike_step,
    _generate_thursday_expiries,
)


def test_black_scholes_pricing():
    # S=2500, K=2500 (ATM), T=0.1 (approx 36 days), r=0.07, sigma=0.18
    prices = _black_scholes(S=2500.0, K=2500.0, T=0.1, r=0.07, sigma=0.18)
    assert "call" in prices and "put" in prices
    assert prices["call"] > 0
    assert prices["put"] > 0
    # At ATM with positive interest rate, Call is slightly higher than Put
    assert prices["call"] >= prices["put"]


def test_strike_step_calculation():
    assert _get_strike_step(45000.0) == 100.0  # BankNifty
    assert _get_strike_step(22000.0) == 50.0   # Nifty
    assert _get_strike_step(2900.0) == 20.0    # Reliance
    assert _get_strike_step(1450.0) == 10.0    # Infy


def test_thursday_expiries():
    expiries = _generate_thursday_expiries(count=4)
    assert len(expiries) == 4
    for exp in expiries:
        assert len(exp.split("-")) == 3


@pytest.mark.asyncio
async def test_options_service_option_chain():
    data = await OptionsService.get_option_chain("RELIANCE")
    assert data["symbol"] == "RELIANCE"
    assert data["underlying_price"] > 0
    assert len(data["expiries"]) >= 1
    assert len(data["chain"]) > 0
    first_row = data["chain"][0]
    assert "strike" in first_row
    assert "call" in first_row
    assert "put" in first_row
    assert data["total_call_oi"] > 0
    assert data["total_put_oi"] > 0
    assert data["pcr_ratio"] is not None


@pytest.mark.asyncio
async def test_options_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/market/options/TCS")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol"] == "TCS"
        assert "chain" in body
        assert len(body["chain"]) > 0
        assert "pcr_ratio" in body
