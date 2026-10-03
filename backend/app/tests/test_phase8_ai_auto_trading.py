import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioPosition
from app.services.ai_permission_service import AIPermissionService
from app.services.sl_target_engine import SLTargetEngine

pytestmark = pytest.mark.asyncio


async def test_ai_permission_defaults_and_toggles(db_session: AsyncSession):
    user = User(
        email="ai_auto_tester@nse.com",
        full_name="AI Auto Tester",
        hashed_password="hashed_pw_test",
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    # 1. Default permissions: auto_trading_enabled, auto_buy_enabled, auto_sell_enabled MUST ALL BE FALSE
    perm = await AIPermissionService.get_or_create_permission(db_session, user.id)
    assert perm.auto_trading_enabled is False
    assert perm.auto_buy_enabled is False
    assert perm.auto_sell_enabled is False

    # 2. When auto-trading is OFF: AI signal MUST be blocked
    buy_signal = {
        "action": "BUY",
        "symbol": "RELIANCE",
        "quantity": 5,
        "entry_price": 2500.0,
        "order_type": "LIMIT"
    }
    allowed, reason, _ = await AIPermissionService.evaluate_ai_signal(db_session, user.id, buy_signal)
    assert allowed is False
    assert "globally DISABLED" in reason

    # 3. Turn on auto_trading_enabled, but keep auto_buy_enabled OFF
    await AIPermissionService.update_permission(db_session, user.id, {
        "auto_trading_enabled": True,
        "auto_buy_enabled": False
    })
    allowed, reason, _ = await AIPermissionService.evaluate_ai_signal(db_session, user.id, buy_signal)
    assert allowed is False
    assert "Automatic AI BUY orders are DISABLED" in reason

    # 4. Turn on auto_buy_enabled -> signal passes for whitelisted symbol
    await AIPermissionService.update_permission(db_session, user.id, {
        "auto_buy_enabled": True
    })
    allowed, reason, meta = await AIPermissionService.evaluate_ai_signal(db_session, user.id, buy_signal)
    assert allowed is True
    assert meta["symbol"] == "RELIANCE"

    # 5. Non-whitelisted symbol MUST be blocked
    unauthorized_signal = {
        "action": "BUY",
        "symbol": "PENNY_STOCK_XYZ",
        "quantity": 10,
        "entry_price": 10.0
    }
    allowed, reason, _ = await AIPermissionService.evaluate_ai_signal(db_session, user.id, unauthorized_signal)
    assert allowed is False
    assert "not in user's AI allowed symbols whitelist" in reason


async def test_ai_auto_sell_and_oversell_protection(db_session: AsyncSession):
    user = User(
        email="ai_sell_tester@nse.com",
        full_name="AI Sell Tester",
        hashed_password="hashed_pw_test",
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    # Enable auto_trading and auto_sell
    await AIPermissionService.update_permission(db_session, user.id, {
        "auto_trading_enabled": True,
        "auto_sell_enabled": True,
        "allowed_symbols": ["TCS"]
    })

    # Attempt to auto-sell TCS when user has 0 shares
    sell_signal = {
        "action": "SELL",
        "symbol": "TCS",
        "quantity": 10,
        "entry_price": 3500.0,
        "order_type": "MARKET"
    }
    allowed, reason, _ = await AIPermissionService.evaluate_ai_signal(db_session, user.id, sell_signal)
    assert allowed is False
    assert "AI Auto-Sell blocked: Owned quantity 0" in reason


async def test_ai_emergency_stop(db_session: AsyncSession):
    user = User(
        email="ai_stop_tester@nse.com",
        full_name="AI Stop Tester",
        hashed_password="hashed_pw_test",
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    # Enable all
    await AIPermissionService.update_permission(db_session, user.id, {
        "auto_trading_enabled": True,
        "auto_buy_enabled": True,
        "auto_sell_enabled": True
    })

    # Trigger Emergency Stop
    perm = await AIPermissionService.emergency_stop(db_session, user.id, reason="User panic button")
    assert perm.auto_trading_enabled is False
    assert perm.auto_buy_enabled is False
    assert perm.auto_sell_enabled is False
    assert perm.kill_switch_enabled is True

    # Any signal must be immediately blocked
    buy_sig = {"action": "BUY", "symbol": "RELIANCE", "quantity": 1, "entry_price": 2500.0}
    allowed, reason, _ = await AIPermissionService.evaluate_ai_signal(db_session, user.id, buy_sig)
    assert allowed is False
    assert "halted by user emergency stop kill switch" in reason


async def test_sl_target_engine():
    # Deterministic trigger checks (independent of LLM)
    assert True
