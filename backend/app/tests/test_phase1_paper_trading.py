import uuid
import pytest
from decimal import Decimal
from app.core.config import Settings
from app.providers.broker.paper_broker import PaperBrokerProvider
from app.services.charge_service import ChargeService


@pytest.mark.asyncio
async def test_trading_environment_endpoint(client):
    res = await client.get("/api/v1/trading/environment")
    assert res.status_code == 200
    data = res.json()
    assert data["trading_mode"] in ["PAPER", "SANDBOX", "LIVE"]
    assert "broker_provider" in data
    assert "is_paper" in data
    assert "is_sandbox" in data
    assert "is_live" in data


def test_trading_environment_compatibility_rules():
    # Valid configurations
    s1 = Settings(TRADING_MODE="PAPER", BROKER_PROVIDER="paper")
    assert s1.is_paper is True

    s2 = Settings(TRADING_MODE="SANDBOX", BROKER_PROVIDER="sandbox")
    assert s2.is_sandbox is True

    # Incompatible: PAPER with live broker
    with pytest.raises(ValueError, match="TRADING_MODE=PAPER cannot run with live broker"):
        Settings(TRADING_MODE="PAPER", BROKER_PROVIDER="zerodha")

    # Incompatible: SANDBOX with live broker
    with pytest.raises(ValueError, match="TRADING_MODE=SANDBOX cannot run with live broker"):
        Settings(TRADING_MODE="SANDBOX", BROKER_PROVIDER="zerodha")

    # Incompatible: LIVE with paper broker
    with pytest.raises(ValueError, match="TRADING_MODE=LIVE cannot run with simulated/paper"):
        Settings(TRADING_MODE="LIVE", BROKER_PROVIDER="paper")


@pytest.mark.asyncio
async def test_paper_broker_provider_methods():
    provider = PaperBrokerProvider()
    assert await provider.connect() is True
    assert await provider.disconnect() is True

    account = await provider.get_account()
    assert account["broker"] == "PAPER_TRADING_SIMULATOR"
    assert account["environment"] == "PAPER"
    assert account["margin_available"] > 0

    balance = await provider.get_balance()
    assert "available_cash" in balance
    assert "locked_margin" in balance

    orders = await provider.get_orders()
    assert isinstance(orders, list)

    positions = await provider.get_positions()
    assert isinstance(positions, list)

    trades = await provider.get_trades()
    assert isinstance(trades, list)

    margins = await provider.get_margins()
    assert isinstance(margins, dict)

    # Simulated order placement
    sim_order = await provider.place_order({
        "symbol": "TCS",
        "side": "BUY",
        "quantity": 5,
        "price": 3800.0,
        "order_type": "MARKET"
    })
    assert sim_order["broker_order_id"].startswith("SIM-")
    assert sim_order["status"] == "FILLED"

    status = await provider.get_order_status(sim_order["broker_order_id"])
    assert status["status"] == "FILLED"


@pytest.mark.asyncio
async def test_paper_partial_sell_and_weighted_average(client):
    reg_payload = {"email": "weighted_avg_trader@nse.com", "password": "Password123!", "full_name": "WA Trader"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "weighted_avg_trader@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    q_res = await client.get("/api/v1/market/quote/TCS")
    tcs_px = float(q_res.json()["price"])
    sl = round(tcs_px * 0.9, 2)
    tgt = round(tcs_px * 1.15, 2)

    # 1. Buy 10 shares
    buy_1 = await client.post("/api/v1/orders", json={
        "symbol": "TCS",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 10,
        "stop_loss": sl,
        "target_price": tgt
    }, headers=headers)
    assert buy_1.status_code == 201
    p1 = float(buy_1.json()["execution_price"])

    # 2. Buy another 15 shares (different quantity to differentiate from rapid duplicate order)
    buy_2 = await client.post("/api/v1/orders", json={
        "symbol": "TCS",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 15,
        "stop_loss": sl
    }, headers=headers)
    assert buy_2.status_code == 201
    p2 = float(buy_2.json()["execution_price"])

    # Verify positions: 25 shares, average price
    pos_res = await client.get("/api/v1/positions", headers=headers)
    assert pos_res.status_code == 200
    pos = next(p for p in pos_res.json()["open_positions"] if p["symbol"] == "TCS")
    assert pos["quantity"] == 25
    expected_avg = round((p1 * 10 + p2 * 15) / 25, 2)
    assert float(pos["average_price"]) == pytest.approx(expected_avg, 0.1)

    # 3. Partial sell: sell 5 shares
    sell_sl = round(tcs_px * 1.15, 2)
    sell_res = await client.post("/api/v1/orders", json={
        "symbol": "TCS",
        "side": "SELL",
        "order_type": "MARKET",
        "quantity": 5,
        "stop_loss": sell_sl
    }, headers=headers)
    assert sell_res.status_code == 201
    sell_data = sell_res.json()
    assert sell_data["status"] == "FILLED"
    assert sell_data["realized_pnl"] is not None

    # Check remaining position has exactly 20 shares
    pos_res_after = await client.get("/api/v1/positions", headers=headers)
    pos_after = next(p for p in pos_res_after.json()["open_positions"] if p["symbol"] == "TCS")
    assert pos_after["quantity"] == 20

    # 4. Check order event history
    order_id = sell_data["id"]
    events_res = await client.get(f"/api/v1/orders/{order_id}/events", headers=headers)
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 2
    event_types = [e["event_type"] for e in events]
    assert "CREATED" in event_types
    assert "FILLED" in event_types
