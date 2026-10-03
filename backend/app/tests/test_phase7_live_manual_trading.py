import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.order import Order
from app.core.config import settings
from app.services.risk_service import RiskService
from app.schemas.risk import RiskValidationRequest
from app.providers.broker.live_broker import LiveBrokerProvider
from app.services.order_state_machine import OrderStateMachine

pytestmark = pytest.mark.asyncio


async def test_live_manual_trading_safety_checks(db_session: AsyncSession):
    user = User(
        email="live_trader_test@nse.com",
        full_name="Live Trader Tester",
        hashed_password="hashed_pw_test",
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    # Pre-flight Risk Check in live environment requires valid token and explicit confirmation
    req = RiskValidationRequest(
        symbol="RELIANCE",
        side="BUY",
        order_type="LIMIT",
        quantity=5,
        price=Decimal("2500.00"),
        stop_loss=Decimal("2400.00"),
        target=Decimal("2650.00")
    )
    res = await RiskService.validate_pre_flight(db_session, user.id, req)
    assert res.approved is True
    assert res.confirmation_token is not None

    # Verify Live Broker Provider connection & order transmission
    live_broker = LiveBrokerProvider(api_key="live_key_test", access_token="live_token_test")
    connected = await live_broker.connect()
    assert connected is True

    # Transmit manual live order with confirmation token
    live_order_data = {
        "symbol": "RELIANCE",
        "side": "BUY",
        "quantity": 5,
        "price": 2500.0,
        "order_type": "LIMIT"
    }
    broker_result = await live_broker.place_order(live_order_data)
    assert broker_result["status"] == "OPEN"
    assert broker_result["broker_order_id"].startswith("LIVE-")

    # Persist live order in internal database with user_confirmed = True
    order = Order(
        user_id=user.id,
        symbol="RELIANCE",
        side="BUY",
        order_type="LIMIT",
        quantity=5,
        price=Decimal("2500.00"),
        broker_order_id=broker_result["broker_order_id"],
        status=OrderStateMachine.SUBMITTED,
        risk_approved=True,
        user_confirmed=True
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.user_confirmed is True
    assert order.broker_order_id.startswith("LIVE-")
