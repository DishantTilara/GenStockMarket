import pytest


@pytest.mark.asyncio
async def test_risk_validation_and_confirmation(client):
    reg_payload = {"email": "risk_trader@nse.com", "password": "Password123!", "full_name": "Risk Tester"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "risk_trader@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Valid risk validation
    valid_req = {
        "symbol": "RELIANCE",
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 10,
        "price": 2980.00,
        "stop_loss": 2900.00
    }
    risk_res = await client.post("/api/v1/orders/validate-risk", json=valid_req, headers=headers)
    assert risk_res.status_code == 200
    r_data = risk_res.json()
    assert r_data["approved"] is True
    assert r_data["confirmation_token"] is not None

    # 2. Invalid stop loss (BUY stop loss higher than price) must reject
    invalid_sl_req = {
        "symbol": "RELIANCE",
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 10,
        "price": 2980.00,
        "stop_loss": 3100.00  # invalid!
    }
    fail_res = await client.post("/api/v1/orders/validate-risk", json=invalid_sl_req, headers=headers)
    assert fail_res.status_code == 200
    assert fail_res.json()["approved"] is False
    assert fail_res.json()["rejection_code"] == "STOP_LOSS_INTEGRITY"

    # 3. Exceeding max order value must reject
    huge_req = {
        "symbol": "RELIANCE",
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 1000,
        "price": 3000.00,
        "stop_loss": 2900.00
    }
    huge_res = await client.post("/api/v1/orders/validate-risk", json=huge_req, headers=headers)
    assert huge_res.status_code == 200
    assert huge_res.json()["approved"] is False
    assert huge_res.json()["rejection_code"] in ["MAX_ORDER_VALUE_LIMIT", "SUFFICIENT_AVAILABLE_FUNDS"]
