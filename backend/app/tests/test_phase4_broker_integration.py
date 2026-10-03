import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import encrypt_broker_secret, decrypt_broker_secret
from app.services.broker_service import BrokerService
from app.providers.broker.factory import get_broker_provider, reset_broker_provider
from app.providers.broker.sandbox_broker import SandboxBrokerProvider
from app.providers.broker.live_broker import LiveBrokerProvider
from app.providers.broker.paper_broker import PaperBrokerProvider

pytestmark = pytest.mark.asyncio


def test_broker_secret_encryption():
    raw_secret = "kite_super_secret_token_12345"
    encrypted = encrypt_broker_secret(raw_secret)
    assert encrypted != raw_secret
    assert raw_secret not in encrypted

    decrypted = decrypt_broker_secret(encrypted)
    assert decrypted == raw_secret

    masked = BrokerService.mask_secret(raw_secret)
    assert masked.endswith("2345")
    assert "kite_super" not in masked


async def test_broker_connect_disconnect_flow(db_session: AsyncSession):
    user = User(
        email="broker_tester@nse.com",
        full_name="Broker Tester",
        hashed_password="pw_test_hashed",
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    # 1. Initial status before connection
    status_before = await BrokerService.get_broker_status(db_session, user.id)
    assert status_before["has_account"] is False

    # 2. Connect broker account
    res = await BrokerService.connect_broker(
        db=db_session,
        user_id=user.id,
        broker_name="zerodha",
        environment="SANDBOX",
        api_key="APIKEY_MOCK_1234",
        api_secret="RAW_SECRET_DO_NOT_EXPOSE_9999",
        client_id="ZER1001"
    )
    assert res["broker_name"] == "zerodha"
    assert res["environment"] == "SANDBOX"
    assert res["is_active"] is True
    assert "RAW_SECRET" not in res["api_key_masked"]

    # 3. Status after connection
    status_after = await BrokerService.get_broker_status(db_session, user.id)
    assert status_after["has_account"] is True
    assert status_after["client_id"] == "ZER1001"
    assert status_after["is_active"] is True

    # Verify secret is encrypted in database
    db_account = await BrokerService.get_active_account(db_session, user.id)
    assert db_account is not None
    assert db_account.encrypted_secret != "RAW_SECRET_DO_NOT_EXPOSE_9999"
    assert decrypt_broker_secret(db_account.encrypted_secret) == "RAW_SECRET_DO_NOT_EXPOSE_9999"

    # 4. Disconnect broker
    disc = await BrokerService.disconnect_broker(db_session, user.id)
    assert disc is True

    status_disconnected = await BrokerService.get_broker_status(db_session, user.id)
    assert status_disconnected["has_account"] is False


async def test_sandbox_broker_lifecycle():
    sbx = SandboxBrokerProvider(api_key="sbx_test_key", client_id="SBX_TEST_01")
    assert await sbx.connect() is True

    # Account info
    acc = await sbx.get_account()
    assert acc["environment"] == "SANDBOX"
    assert acc["is_connected"] is True

    # Balances
    bal = await sbx.get_balance()
    assert bal["cash_balance"] > 0
    assert bal["available_margin"] > 0

    # Place Order
    order_data = {
        "symbol": "INFY",
        "side": "BUY",
        "quantity": 10,
        "price": 1500.0,
        "order_type": "LIMIT"
    }
    ord_res = await sbx.place_order(order_data)
    assert ord_res["status"] == "FILLED"
    assert ord_res["filled_quantity"] == 10
    assert ord_res["symbol"] == "INFY"

    # Check Positions
    positions = await sbx.get_positions()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "INFY"
    assert positions[0]["quantity"] == 10

    # Rejection Simulation
    reject_res = await sbx.place_order({
        "symbol": "REJECT_ME",
        "side": "BUY",
        "quantity": 5,
        "price": 100.0
    })
    assert reject_res["status"] == "REJECTED"


def test_factory_provider_resolution():
    reset_broker_provider()
    paper = get_broker_provider("paper")
    assert isinstance(paper, PaperBrokerProvider)

    reset_broker_provider()
    sbx = get_broker_provider("sandbox")
    assert isinstance(sbx, SandboxBrokerProvider)

    reset_broker_provider()
    live = get_broker_provider("live")
    assert isinstance(live, LiveBrokerProvider)


async def test_broker_api_endpoints(client):
    # Register & Login
    reg_payload = {"email": "broker_api_user@nse.com", "password": "Password123!", "full_name": "Broker API User"}
    await client.post("/api/v1/auth/register", json=reg_payload)
    login_res = await client.post("/api/v1/auth/login", json={"email": "broker_api_user@nse.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/v1/broker/status
    res = await client.get("/api/v1/broker/status", headers=headers)
    assert res.status_code == 200

    # 2. POST /api/v1/broker/connect
    conn_res = await client.post("/api/v1/broker/connect", json={
        "broker_name": "angelone",
        "environment": "SANDBOX",
        "api_key": "ANGEL_KEY_999",
        "api_secret": "ANGEL_SECRET_TOKEN_444",
        "client_id": "ANGEL_CLI_01"
    }, headers=headers)
    assert conn_res.status_code == 201
    conn_data = conn_res.json()
    assert conn_data["broker_name"] == "angelone"
    assert "ANGEL_SECRET" not in str(conn_data)

    # 3. GET /api/v1/broker/margins
    margin_res = await client.get("/api/v1/broker/margins", headers=headers)
    assert margin_res.status_code == 200

    # 4. GET /health/broker
    health_res = await client.get("/health/broker")
    assert health_res.status_code == 200
    assert "status" in health_res.json()
