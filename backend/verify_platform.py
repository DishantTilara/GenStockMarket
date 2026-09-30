import asyncio
import httpx
import json
import sys

# Ensure UTF-8 output on Windows console
sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

async def test_platform():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("\n--- 1. Testing Health Endpoints ---")
        res = await client.get("/health")
        print("GET /health:", res.status_code, res.json())
        assert res.status_code == 200

        res = await client.get("/health/market")
        print("GET /health/market:", res.status_code, res.json())
        assert res.status_code == 200
        assert res.json()["provider"] == "connected"

        print("\n--- 2. Testing Authentication ---")
        reg_payload = {
            "email": "trader@dalalstreet.ai",
            "password": "SecurePassword123!",
            "full_name": "Pro Indian Trader"
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        if res.status_code == 400: # Already registered
            print("User already registered, logging in...")
        else:
            print("User registered:", res.status_code)

        login_res = await client.post("/api/v1/auth/login", json={
            "email": "trader@dalalstreet.ai",
            "password": "SecurePassword123!"
        })
        print("Login status:", login_res.status_code)
        assert login_res.status_code == 200
        token_data = login_res.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("JWT Token acquired successfully.")

        print("\n--- 3. Testing Wallet & Ledger ---")
        wallet_res = await client.get("/api/v1/wallet", headers=headers)
        print("GET /wallet:", wallet_res.status_code, wallet_res.json())
        assert wallet_res.status_code == 200

        # Deposit funds (Idempotent, double-entry ledger)
        import uuid
        deposit_payload = {
            "amount": 250000.00,
            "idempotency_key": f"DEP-{uuid.uuid4().hex[:8]}"
        }
        dep_res = await client.post("/api/v1/wallet/deposit", json=deposit_payload, headers=headers)
        print("POST /wallet/deposit (INR 250,000):", dep_res.status_code, dep_res.json())
        assert dep_res.status_code == 200

        tx_res = await client.get("/api/v1/wallet/transactions", headers=headers)
        tx_data = tx_res.json()
        tx_list = tx_data if isinstance(tx_data, list) else tx_data.get("data", [])
        print("GET /wallet/transactions count:", len(tx_list))
        assert len(tx_list) >= 1

        print("\n--- 4. Testing Market Data & Indicators ---")
        inst_res = await client.get("/api/v1/market/instruments")
        print("GET /market/instruments count:", len(inst_res.json()))

        quote_res = await client.get("/api/v1/market/quote/RELIANCE")
        print("GET /market/quote/RELIANCE:", quote_res.json()["symbol"], "LTP:", quote_res.json()["price"])

        ind_res = await client.get("/api/v1/technical/RELIANCE")
        print("GET /technical/RELIANCE:", ind_res.status_code)
        indicators = ind_res.json()
        print(f"RSI: {indicators.get('rsi_14')}, EMA20: {indicators.get('ema_20')}, VWAP: {indicators.get('vwap')}")

        print("\n--- 5. Testing AI Stock Analyst (Tool-Grounded) ---")
        ai_res = await client.get("/api/v1/ai/stock/RELIANCE", headers=headers)
        print("GET /ai/stock/RELIANCE status:", ai_res.status_code)
        assert ai_res.status_code == 200
        analysis = ai_res.json()
        print("AI Signal:", analysis.get("signal"))
        print("Market Regime:", analysis.get("market_regime"))
        print("Confidence:", analysis.get("confidence"))
        print("Supporting Factors:", analysis.get("supporting_factors"))
        print("Warnings:", analysis.get("warnings"))
        assert analysis.get("signal") in ["BUY", "SELL", "WATCH", "NO_TRADE", "INSUFFICIENT_DATA"]

        print("\n--- 6. Testing Pre-Trade Risk Engine & Human Approval ---")
        # Validate trade setup (passes through 6-point risk gate)
        trade_setup = {
            "symbol": "RELIANCE",
            "side": "BUY",
            "order_type": "LIMIT",
            "quantity": 10,
            "price": float(quote_res.json()["price"]),
            "stop_loss": round(float(quote_res.json()["price"]) * 0.98, 2),
            "target": round(float(quote_res.json()["price"]) * 1.04, 2)
        }
        val_res = await client.post("/api/v1/orders/validate-risk", json=trade_setup, headers=headers)
        print("POST /orders/validate-risk:", val_res.status_code, val_res.json())
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert val_data["approved"] is True
        token = val_data["confirmation_token"]
        print("Risk Gate Passed. Received Confirmation Token:", token[:16] + "...")

        # Now test human-confirmed order execution via Paper Broker Provider
        exec_payload = {
            "confirmation_token": token,
            "symbol": "RELIANCE",
            "side": "BUY",
            "order_type": "LIMIT",
            "quantity": 10,
            "price": float(quote_res.json()["price"]),
            "stop_loss": round(float(quote_res.json()["price"]) * 0.98, 2),
            "target": round(float(quote_res.json()["price"]) * 1.04, 2)
        }
        order_res = await client.post("/api/v1/orders/execute", json=exec_payload, headers=headers)
        print("POST /orders/execute:", order_res.status_code, order_res.json())
        assert order_res.status_code == 200
        assert order_res.json()["status"] == "FILLED"

        # Check updated positions and portfolio
        port_res = await client.get("/api/v1/portfolio", headers=headers)
        print("GET /portfolio positions:", len(port_res.json()["positions"]))

        print("\n--- 7. Testing Backtest Engine ---")
        backtest_req = {
            "symbol": "RELIANCE",
            "initial_capital": 500000.0,
            "timeframe": "1d",
            "days_back": 60,
            "entry_rules": ["close > EMA20", "RSI > 55"],
            "exit_rules": ["close < EMA20"],
            "stop_loss_pct": 2.0,
            "target_pct": 5.0,
            "slippage_pct": 0.05,
            "brokerage_per_trade": 20.0
        }
        bt_res = await client.post("/api/v1/backtests/run", json=backtest_req, headers=headers)
        print("POST /backtests/run:", bt_res.status_code)
        assert bt_res.status_code == 200
        bt_result = bt_res.json()
        print(f"Total Return: {bt_result['total_return']}% | Trades: {bt_result['trade_count']} | Win Rate: {bt_result['win_rate']}% | Max DD: {bt_result['max_drawdown']}% | Sharpe: {bt_result['sharpe_ratio']}")

        print("\n=======================================================")
        print(" ALL END-TO-END VERIFICATION TESTS PASSED SUCCESSFULLY! ")
        print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(test_platform())
