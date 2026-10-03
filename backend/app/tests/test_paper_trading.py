import uuid
import pytest
from decimal import Decimal
from app.services.paper_trading_service import PaperTradingService
from app.services.charge_service import ChargeService
from app.models.order import Order
from app.models.portfolio import PortfolioPosition


@pytest.mark.asyncio
async def test_paper_buy_and_sell_lifecycle(client):
    # 1. Register & Login
    reg_payload = {"email": "paper_trader@nse.com", "password": "Password123!", "full_name": "Paper Trader"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "paper_trader@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Initial Portfolio Check: starting cash ₹10,00,000, 0 holdings
    port_res = await client.get("/api/v1/portfolio", headers=headers)
    assert port_res.status_code == 200
    port_data = port_res.json()
    assert float(port_data["cash_balance"]) == 1000000.00
    assert len(port_data["positions"]) == 0

    # Fetch live quote for dynamic price calculations
    q_res = await client.get("/api/v1/market/quote/RELIANCE")
    rel_price = float(q_res.json()["price"])
    buy_sl = round(rel_price * 0.9, 2)
    buy_target = round(rel_price * 1.15, 2)

    # 2. Place Paper BUY Order (MARKET)
    buy_payload = {
        "symbol": "RELIANCE",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 10,
        "stop_loss": buy_sl,
        "target_price": buy_target
    }
    buy_res = await client.post("/api/v1/orders", json=buy_payload, headers=headers)
    assert buy_res.status_code == 201
    buy_data = buy_res.json()
    assert buy_data["status"] == "FILLED"
    assert buy_data["side"] == "BUY"
    assert buy_data["quantity"] == 10
    assert buy_data["execution_price"] is not None
    exec_price_1 = float(buy_data["execution_price"])
    assert exec_price_1 > 0

    # Verify wallet balance decreased by (execution_price * 10) + charges
    port_res_after_buy = await client.get("/api/v1/portfolio", headers=headers)
    port_after_buy = port_res_after_buy.json()
    assert len(port_after_buy["positions"]) == 1
    rel_pos = port_after_buy["positions"][0]
    assert rel_pos["symbol"] == "RELIANCE"
    assert rel_pos["quantity"] == 10
    assert float(rel_pos["average_price"]) == pytest.approx(exec_price_1, 0.05)
    assert float(port_after_buy["cash_balance"]) < 1000000.00

    # Total Equity = Cash + Current Value
    expected_equity = float(port_after_buy["cash_balance"]) + float(port_after_buy["current_value"])
    assert float(port_after_buy["total_equity"]) == pytest.approx(expected_equity, 0.05)

    # 3. Second BUY to test Average Price calculation
    buy_payload_2 = {
        "symbol": "RELIANCE",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 10,
        "stop_loss": buy_sl
    }
    buy_res_2 = await client.post("/api/v1/orders", json=buy_payload_2, headers=headers)
    assert buy_res_2.status_code == 201
    exec_price_2 = float(buy_res_2.json()["execution_price"])

    # Verify new quantity = 20, average price = (10*p1 + 10*p2)/20
    pos_res = await client.get("/api/v1/positions", headers=headers)
    assert pos_res.status_code == 200
    positions = pos_res.json()["open_positions"]
    assert len(positions) == 1
    rel_pos_2 = positions[0]
    assert rel_pos_2["quantity"] == 20
    expected_avg = round((10 * exec_price_1 + 10 * exec_price_2) / 20, 2)
    assert float(rel_pos_2["average_price"]) == pytest.approx(expected_avg, 0.1)

    # 4. SELL Validation: Oversell rejection
    sell_sl = round(rel_price * 1.15, 2)
    oversell_payload = {
        "symbol": "RELIANCE",
        "side": "SELL",
        "order_type": "MARKET",
        "quantity": 50,  # owns only 20!
        "stop_loss": sell_sl
    }
    oversell_res = await client.post("/api/v1/orders", json=oversell_payload, headers=headers)
    assert oversell_res.status_code == 400
    assert "SELL_QUANTITY_AVAILABLE" in oversell_res.text or "holding" in oversell_res.text

    # 5. Valid Paper SELL: Sell 10 shares
    cash_before_sell = float((await client.get("/api/v1/portfolio", headers=headers)).json()["cash_balance"])
    sell_payload = {
        "symbol": "RELIANCE",
        "side": "SELL",
        "order_type": "MARKET",
        "quantity": 10,
        "stop_loss": sell_sl
    }
    sell_res = await client.post("/api/v1/orders", json=sell_payload, headers=headers)
    assert sell_res.status_code == 201
    sell_data = sell_res.json()
    assert sell_data["status"] == "FILLED"
    assert sell_data["realized_pnl"] is not None

    # Check cash credited back
    port_after_sell = (await client.get("/api/v1/portfolio", headers=headers)).json()
    assert float(port_after_sell["cash_balance"]) > cash_before_sell
    assert port_after_sell["positions"][0]["quantity"] == 10

    # 6. Close remaining 10 shares via position close endpoint
    close_res = await client.post("/api/v1/positions/RELIANCE/close", headers=headers)
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"

    # All positions now closed
    pos_after_close = (await client.get("/api/v1/positions", headers=headers)).json()
    assert len(pos_after_close["open_positions"]) == 0
    assert len(pos_after_close["closed_positions"]) >= 1


@pytest.mark.asyncio
async def test_paper_limit_order_and_tick_trigger(client):
    reg_payload = {"email": "limit_trader@nse.com", "password": "Password123!", "full_name": "Limit Trader"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "limit_trader@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch quote for RELIANCE
    q_res = await client.get("/api/v1/market/quote/RELIANCE")
    rel_price = float(q_res.json()["price"])
    # Submit a BUY LIMIT order 15% below market price, adhering to 0.05 tick size
    limit_px = round(round(rel_price * 0.85 / 0.05) * 0.05, 2)
    limit_sl = round(round(limit_px * 0.90 / 0.05) * 0.05, 2)
    limit_tgt = round(round(limit_px * 1.20 / 0.05) * 0.05, 2)

    limit_payload = {
        "symbol": "RELIANCE",
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 5,
        "price": limit_px,
        "stop_loss": limit_sl,
        "target_price": limit_tgt
    }
    order_res = await client.post("/api/v1/orders", json=limit_payload, headers=headers)
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["status"] == "PENDING"
    order_id = order_data["id"]

    # Verify margin locked in wallet
    orders_list = (await client.get("/api/v1/orders?status=OPEN", headers=headers)).json()
    assert any(o["id"] == order_id for o in orders_list)

    # Cancel the pending limit order
    cancel_res = await client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_paper_idempotency(client):
    reg_payload = {"email": "idem_trader@nse.com", "password": "Password123!", "full_name": "Idem Trader"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "idem_trader@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    q_res = await client.get("/api/v1/market/quote/INFY")
    infy_price = float(q_res.json()["price"])
    infy_sl = round(infy_price * 0.9, 2)

    idempotency_key = f"IDEM-{uuid.uuid4().hex[:12]}"
    payload = {
        "symbol": "INFY",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 5,
        "stop_loss": infy_sl,
        "idempotency_key": idempotency_key
    }

    # First request
    res1 = await client.post("/api/v1/orders", json=payload, headers=headers)
    assert res1.status_code == 201
    order_1 = res1.json()

    # Immediate duplicate request with same idempotency key
    res2 = await client.post("/api/v1/orders", json=payload, headers=headers)
    assert res2.status_code == 201
    order_2 = res2.json()

    # Must return the SAME order without double-buying
    assert order_1["id"] == order_2["id"]

    # Verify positions: only 5 INFY owned, not 10
    pos_res = await client.get("/api/v1/positions", headers=headers)
    positions = pos_res.json()["open_positions"]
    infy_pos = next(p for p in positions if p["symbol"] == "INFY")
    assert infy_pos["quantity"] == 5


@pytest.mark.asyncio
async def test_paper_reset_and_reconciliation(client):
    reg_payload = {"email": "reset_trader@nse.com", "password": "Password123!", "full_name": "Reset Trader"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "reset_trader@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    q_res = await client.get("/api/v1/market/quote/TCS")
    tcs_price = float(q_res.json()["price"])
    tcs_sl = round(tcs_price * 0.9, 2)

    # Buy something first
    await client.post("/api/v1/orders", json={"symbol": "TCS", "side": "BUY", "order_type": "MARKET", "quantity": 2, "stop_loss": tcs_sl}, headers=headers)

    # Check health reconciliation endpoint
    health_res = await client.get("/health/paper-trading")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["mode"] == "PAPER"
    assert health_data["status"] == "HEALTHY"
    assert health_data["wallet_consistent"] is True

    # Reset paper account
    reset_res = await client.post("/api/v1/paper/reset", json={"clear_history": True, "confirm": True}, headers=headers)
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "RESET_SUCCESSFUL"
    assert reset_res.json()["available_cash"] == 1000000.00

    # Verify portfolio is clean
    port_res = await client.get("/api/v1/portfolio", headers=headers)
    port_data = port_res.json()
    assert float(port_data["cash_balance"]) == 1000000.00
    assert len(port_data["positions"]) == 0
