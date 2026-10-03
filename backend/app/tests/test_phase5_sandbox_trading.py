import pytest
from decimal import Decimal
from app.providers.broker.sandbox_broker import SandboxBrokerProvider

pytestmark = pytest.mark.asyncio


async def test_sandbox_trading_flow():
    provider = SandboxBrokerProvider(api_key="sbx_api_key", client_id="SBX_TRADER_001")
    connected = await provider.connect()
    assert connected is True

    # Initial balance check
    bal_initial = await provider.get_balance()
    assert bal_initial["cash_balance"] == 2000000.00
    assert bal_initial["available_margin"] == 2000000.00

    # 1. Place Sandbox Buy Order
    order_1 = await provider.place_order({
        "symbol": "TCS",
        "side": "BUY",
        "quantity": 10,
        "price": 3200.0,
        "order_type": "LIMIT"
    })
    assert order_1["status"] == "FILLED"
    assert order_1["broker_order_id"].startswith("SBX-")
    assert order_1["filled_quantity"] == 10
    assert order_1["average_price"] == 3200.0

    # Verify positions and updated margin
    positions = await provider.get_positions()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "TCS"
    assert positions[0]["quantity"] == 10

    bal_after = await provider.get_balance()
    assert bal_after["used_margin"] == 32000.00
    assert bal_after["available_margin"] == 2000000.00 - 32000.00

    # 2. Place Partial Sandbox Sell Order (sell 4 shares)
    order_sell = await provider.place_order({
        "symbol": "TCS",
        "side": "SELL",
        "quantity": 4,
        "price": 3300.0,
        "order_type": "MARKET"
    })
    assert order_sell["status"] == "FILLED"

    positions_after_sell = await provider.get_positions()
    assert len(positions_after_sell) == 1
    assert positions_after_sell[0]["quantity"] == 6

    # 3. Simulated Rejection for Symbol
    rejected_order = await provider.place_order({
        "symbol": "REJECT_ME",
        "side": "BUY",
        "quantity": 10,
        "price": 500.0
    })
    assert rejected_order["status"] == "REJECTED"
    assert "reason" in rejected_order
