import pytest


@pytest.mark.asyncio
async def test_wallet_deposit_withdrawal_and_ledger(client):
    # Register & Login
    reg_payload = {"email": "wallet_user@nse.com", "password": "Password123!", "full_name": "Radhakishan Damani"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "wallet_user@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check initial wallet
    wallet_res = await client.get("/api/v1/wallet", headers=headers)
    assert wallet_res.status_code == 200
    w_data = wallet_res.json()
    assert float(w_data["available_balance"]) >= 100000.0

    # 2. Deposit Funds
    deposit_payload = {
        "amount": 25000.00,
        "idempotency_key": "DEP-TEST-12345678",
        "payment_method": "simulated_upi"
    }
    dep_res = await client.post("/api/v1/wallet/deposit", json=deposit_payload, headers=headers)
    assert dep_res.status_code == 200
    assert float(dep_res.json()["amount"]) == 25000.00

    # 3. Duplicate idempotency key must reject
    dup_res = await client.post("/api/v1/wallet/deposit", json=deposit_payload, headers=headers)
    assert dup_res.status_code == 400
    assert dup_res.json()["error"]["code"] == "DUPLICATE_IDEMPOTENCY_KEY"

    # 4. Withdraw Funds
    wth_payload = {
        "amount": 10000.00,
        "bank_account_info": "HDFC0001234-9988776655"
    }
    wth_res = await client.post("/api/v1/wallet/withdraw", json=wth_payload, headers=headers)
    assert wth_res.status_code == 200
    assert float(wth_res.json()["amount"]) == 10000.00

    # 5. Over-withdrawal must reject with INSUFFICIENT_FUNDS
    over_payload = {"amount": 999999999.00, "bank_account_info": "HDFC0001234-9988776655"}
    over_res = await client.post("/api/v1/wallet/withdraw", json=over_payload, headers=headers)
    assert over_res.status_code == 400
    assert over_res.json()["error"]["code"] == "INSUFFICIENT_FUNDS"

    # 6. Check ledger transactions
    tx_res = await client.get("/api/v1/wallet/transactions", headers=headers)
    assert tx_res.status_code == 200
    entries = tx_res.json()
    assert len(entries) >= 2
    types = [e["entry_type"] for e in entries]
    assert "DEPOSIT" in types
    assert "WITHDRAWAL_LOCK" in types
