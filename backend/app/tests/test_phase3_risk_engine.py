import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.wallet import Wallet
from app.models.risk import RiskSettings, KillSwitch, RiskEvent
from app.services.risk_service import RiskService
from app.services.wallet_service import WalletService
from app.schemas.risk import OrderCreateRequest

pytestmark = pytest.mark.asyncio


async def test_kill_switches(db_session: AsyncSession):
    # Setup test user
    user = User(
        email="risk_test@example.com",
        full_name="Risk Tester",
        hashed_password="hashed_pw_test",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Create wallet with funds
    await WalletService.get_or_create_wallet(db_session, user.id)

    order_req = OrderCreateRequest(
        symbol="TCS",
        order_type="LIMIT",
        side="BUY",
        quantity=5,
        price=Decimal("3500.00"),
        stop_loss=Decimal("3400.00"),
        target=Decimal("3650.00"),
    )

    # 1. Normal state should pass initial kill switch check
    passed, reason = await RiskService.validate_order(db_session, user.id, order_req, Decimal("3500.00"))
    assert passed, f"Expected order to pass, but got: {reason}"

    # 2. Activate Platform Kill Switch
    await RiskService.toggle_kill_switch(db_session, scope="PLATFORM", is_active=True, reason="Emergency platform halt")
    passed, reason = await RiskService.validate_order(db_session, user.id, order_req, Decimal("3500.00"))
    assert not passed
    assert "Platform trading currently suspended" in reason

    # 3. Deactivate Platform Kill Switch
    await RiskService.toggle_kill_switch(db_session, scope="PLATFORM", is_active=False)

    # 4. Activate User Kill Switch
    await RiskService.toggle_kill_switch(db_session, scope="USER", user_id=user.id, is_active=True, reason="User panic halt")
    passed, reason = await RiskService.validate_order(db_session, user.id, order_req, Decimal("3500.00"))
    assert not passed
    assert "User trading halted" in reason

    # 5. Deactivate User Kill Switch
    await RiskService.toggle_kill_switch(db_session, scope="USER", user_id=user.id, is_active=False)
    passed, reason = await RiskService.validate_order(db_session, user.id, order_req, Decimal("3500.00"))
    assert passed, f"Order should pass after user kill switch deactivated, got: {reason}"


async def test_risk_settings_and_limits(db_session: AsyncSession):
    user = User(
        email="limits_test@example.com",
        full_name="Limits Tester",
        hashed_password="hashed_pw_test",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    await WalletService.get_or_create_wallet(db_session, user.id)

    # Update settings to cap max_order_value at 20,000 and max_quantity at 10
    await RiskService.update_user_settings(db_session, user.id, {
        "max_order_value": Decimal("20000.00"),
        "max_quantity": 10
    })

    # Order value = 10 * 3000 = 30,000 > 20,000
    order_exceeds = OrderCreateRequest(
        symbol="INFY",
        order_type="LIMIT",
        side="BUY",
        quantity=10,
        price=Decimal("3000.00"),
    )
    passed, reason = await RiskService.validate_order(db_session, user.id, order_exceeds, Decimal("3000.00"))
    assert not passed
    assert "Max allowed" in reason

    # Exceeds max quantity (15 > 10)
    order_qty_exceeds = OrderCreateRequest(
        symbol="INFY",
        order_type="LIMIT",
        side="BUY",
        quantity=15,
        price=Decimal("1000.00"),
    )
    passed, reason = await RiskService.validate_order(db_session, user.id, order_qty_exceeds, Decimal("1000.00"))
    assert not passed
    assert "Quantity must be between" in reason


async def test_oversell_and_events_logging(db_session: AsyncSession):
    user = User(
        email="oversell_test@example.com",
        full_name="Oversell Tester",
        hashed_password="hashed_pw_test",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    await WalletService.get_or_create_wallet(db_session, user.id)

    # Attempt to sell shares not owned
    sell_req = OrderCreateRequest(
        symbol="RELIANCE",
        order_type="MARKET",
        side="SELL",
        quantity=10,
    )
    passed, reason = await RiskService.validate_order(db_session, user.id, sell_req, Decimal("900.00"))
    assert not passed
    assert "vs Owned holding" in reason

    # Verify risk events were logged
    events = await RiskService.get_risk_events(db_session, user_id=user.id)
    assert len(events) >= 1
    event = events[0]
    assert event.passed is False
    assert event.severity == "BLOCK"
    assert event.rejection_code == "SELL_QUANTITY_AVAILABLE"
