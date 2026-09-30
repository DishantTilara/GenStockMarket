import pytest


@pytest.mark.asyncio
async def test_backtest_execution(client):
    reg_payload = {"email": "quant_trader@nse.com", "password": "Password123!", "full_name": "Quant Tester"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "quant_trader@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    bt_req = {
        "symbol": "TCS",
        "timeframe": "5m",
        "days_back": 15,
        "initial_capital": 100000.00,
        "stop_loss_pct": 1.5,
        "target_pct": 3.0
    }
    bt_res = await client.post("/api/v1/backtests/run", json=bt_req, headers=headers)
    assert bt_res.status_code == 200
    data = bt_res.json()
    assert data["symbol"] == "TCS"
    assert "total_return" in data
    assert "win_rate" in data
    assert "equity_curve" in data
    assert len(data["equity_curve"]) > 0
