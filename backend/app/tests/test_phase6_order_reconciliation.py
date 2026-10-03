import pytest
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.order import Order, OrderEvent
from app.models.broker import BrokerAccount, BrokerReconciliationEvent
from app.services.order_state_machine import OrderStateMachine
from app.services.broker_reconciliation_service import BrokerReconciliationService
from app.providers.broker.factory import get_broker_provider, reset_broker_provider

pytestmark = pytest.mark.asyncio


async def test_order_state_machine_transitions(db_session: AsyncSession):
    user = User(
        email="osm_tester@nse.com",
        full_name="OSM Tester",
        hashed_password="pw_test_hashed",
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        user_id=user.id,
        symbol="RELIANCE",
        side="BUY",
        order_type="LIMIT",
        quantity=5,
        price=Decimal("2500.00"),
        status=OrderStateMachine.CREATED
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # 1. Valid transitions: CREATED -> RISK_PENDING -> RISK_APPROVED -> SUBMITTED -> OPEN -> FILLED
    await OrderStateMachine.transition(db_session, order, OrderStateMachine.RISK_PENDING)
    assert order.status == OrderStateMachine.RISK_PENDING

    await OrderStateMachine.transition(db_session, order, OrderStateMachine.RISK_APPROVED)
    assert order.status == OrderStateMachine.RISK_APPROVED

    await OrderStateMachine.transition(db_session, order, OrderStateMachine.SUBMITTED)
    assert order.status == OrderStateMachine.SUBMITTED

    await OrderStateMachine.transition(db_session, order, OrderStateMachine.OPEN)
    assert order.status == OrderStateMachine.OPEN

    await OrderStateMachine.transition(db_session, order, OrderStateMachine.FILLED)
    assert order.status == OrderStateMachine.FILLED

    # 2. Verify illegal transition: FILLED -> CREATED must raise ValueError
    with pytest.raises(ValueError, match="Illegal order state transition"):
        await OrderStateMachine.transition(db_session, order, OrderStateMachine.CREATED)

    # Verify illegal transition: CANCELLED -> FILLED
    order_cancelled = Order(
        user_id=user.id,
        symbol="INFY",
        side="BUY",
        order_type="MARKET",
        quantity=10,
        price=Decimal("1500.00"),
        status=OrderStateMachine.CANCELLED
    )
    db_session.add(order_cancelled)
    await db_session.commit()
    await db_session.refresh(order_cancelled)

    with pytest.raises(ValueError, match="Illegal order state transition"):
        await OrderStateMachine.transition(db_session, order_cancelled, OrderStateMachine.FILLED)

    # 3. Check OrderEvents logged in DB
    events_res = await db_session.execute(
        select(OrderEvent).where(OrderEvent.order_id == order.id)
    )
    events = events_res.scalars().all()
    assert len(events) >= 5


async def test_broker_reconciliation_detection_and_auto_correction(db_session: AsyncSession):
    user = User(
        email="reconcile_tester@nse.com",
        full_name="Reconcile Tester",
        hashed_password="pw_test_hashed",
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    # Active broker account
    acct = BrokerAccount(
        user_id=user.id,
        broker_name="sandbox",
        environment="SANDBOX",
        client_id="REC_CLI_01",
        is_active=True
    )
    db_session.add(acct)
    await db_session.flush()

    # Setup Sandbox provider with an order that is FILLED on broker
    reset_broker_provider()
    sbx = get_broker_provider("sandbox")
    await sbx.connect()

    broker_ord = await sbx.place_order({
        "symbol": "WIPRO",
        "side": "BUY",
        "quantity": 20,
        "price": 450.0
    })
    b_id = broker_ord["broker_order_id"]

    # In internal DB, create matching order but simulate lag: still marked SUBMITTED
    db_order = Order(
        user_id=user.id,
        symbol="WIPRO",
        side="BUY",
        order_type="LIMIT",
        quantity=20,
        price=Decimal("450.00"),
        broker_order_id=b_id,
        status=OrderStateMachine.SUBMITTED
    )
    db_session.add(db_order)
    await db_session.commit()
    await db_session.refresh(db_order)

    # Run reconciliation: Should detect STATUS_MISMATCH and auto-correct DB to FILLED
    result = await BrokerReconciliationService.reconcile_account(db_session, user.id, auto_correct=True)
    assert result["discrepancies_detected"] >= 1
    assert result["corrections_applied"] >= 1

    # Verify DB order is now FILLED
    await db_session.refresh(db_order)
    assert db_order.status == OrderStateMachine.FILLED

    # Check that BrokerReconciliationEvent was logged
    events = await BrokerReconciliationService.get_reconciliation_events(db_session, user.id)
    assert len(events) >= 1
    discrepancy_types = [e["discrepancy_type"] for e in events]
    assert "STATUS_MISMATCH" in discrepancy_types
