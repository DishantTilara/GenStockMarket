import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.ai_trading import AITradingPermission
from app.models.portfolio import Portfolio, PortfolioPosition
from app.core.audit import log_audit_event

logger = logging.getLogger("ai_permission_service")


class AIPermissionService:
    """
    Authoritative AI Trading Permission Engine.
    Enforces that AI can NEVER directly execute orders without passing
    strict user-defined automatic trading permissions.
    """

    ALLOWED_ACTIONS = {"BUY", "SELL", "WATCH", "NO_TRADE", "INSUFFICIENT_DATA"}

    @classmethod
    async def get_or_create_permission(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> AITradingPermission:
        stmt = select(AITradingPermission).where(AITradingPermission.user_id == user_id)
        res = await db.execute(stmt)
        perm = res.scalar_one_or_none()
        if not perm:
            perm = AITradingPermission(
                user_id=user_id,
                auto_trading_enabled=False,
                auto_buy_enabled=False,
                auto_sell_enabled=False,
                require_risk_approval=True,
                max_order_value=Decimal("50000.00"),
                max_daily_loss=Decimal("15000.00"),
                max_position_value=Decimal("100000.00"),
                max_open_positions=5,
                max_daily_orders=20,
                allowed_symbols=["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"],
                allowed_exchanges=["NSE"],
                allowed_order_types=["LIMIT", "MARKET"],
                start_time="09:15",
                end_time="15:15",
                kill_switch_enabled=False
            )
            db.add(perm)
            await db.commit()
            await db.refresh(perm)
        return perm

    @classmethod
    async def update_permission(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        updates: Dict[str, Any]
    ) -> AITradingPermission:
        perm = await cls.get_or_create_permission(db, user_id)
        for k, v in updates.items():
            if hasattr(perm, k):
                if k in ["max_order_value", "max_daily_loss", "max_position_value"] and v is not None:
                    setattr(perm, k, Decimal(str(v)))
                else:
                    setattr(perm, k, v)
        await db.commit()
        await db.refresh(perm)

        await log_audit_event(
            db=db,
            action="AI_PERMISSION_UPDATED",
            user_id=user_id,
            resource_type="ai_trading_permission",
            resource_id=str(perm.id),
            details={"auto_trading_enabled": perm.auto_trading_enabled}
        )
        return perm

    @classmethod
    async def emergency_stop(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        reason: str = "User triggered Emergency Stop"
    ) -> AITradingPermission:
        perm = await cls.get_or_create_permission(db, user_id)
        perm.auto_trading_enabled = False
        perm.auto_buy_enabled = False
        perm.auto_sell_enabled = False
        perm.kill_switch_enabled = True
        await db.commit()
        await db.refresh(perm)

        await log_audit_event(
            db=db,
            action="AI_EMERGENCY_STOP_TRIGGERED",
            user_id=user_id,
            resource_type="ai_trading_permission",
            resource_id=str(perm.id),
            details={"reason": reason}
        )
        logger.warning(f"[AI PERMISSION] Emergency stop triggered for user {user_id}: {reason}")
        return perm

    @classmethod
    async def evaluate_ai_signal(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        signal: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates structured AI signal against user's AI Trading Permissions.
        Returns: (allowed: bool, reason: str, metadata: dict)
        """
        action = signal.get("action", "").upper()
        symbol = signal.get("symbol", "").upper()
        quantity = int(signal.get("quantity", 0))
        price = Decimal(str(signal.get("entry_price") or signal.get("price") or "0.00"))
        order_type = signal.get("order_type", "LIMIT").upper()

        # 1. Action Validation
        if action not in cls.ALLOWED_ACTIONS:
            return False, f"Invalid AI action '{action}'. Allowed: {list(cls.ALLOWED_ACTIONS)}", {}

        if action in ["WATCH", "NO_TRADE", "INSUFFICIENT_DATA"]:
            return False, f"AI signal specifies non-executable action: {action}", {}

        # 2. Retrieve user permission settings
        perm = await cls.get_or_create_permission(db, user_id)

        # 3. Master Kill Switch & Auto-trading switches
        if perm.kill_switch_enabled:
            return False, "AI Auto-Trading is halted by user emergency stop kill switch", {}

        if not perm.auto_trading_enabled:
            return False, "AI Auto-Trading is globally DISABLED in user settings", {}

        if action == "BUY" and not perm.auto_buy_enabled:
            return False, "Automatic AI BUY orders are DISABLED in user settings", {}

        if action == "SELL" and not perm.auto_sell_enabled:
            return False, "Automatic AI SELL orders are DISABLED in user settings", {}

        # 4. Symbol Filter
        if symbol not in [s.upper() for s in (perm.allowed_symbols or [])]:
            return False, f"Symbol {symbol} is not in user's AI allowed symbols whitelist", {}

        # 5. Order Type Filter
        if order_type not in [ot.upper() for ot in (perm.allowed_order_types or [])]:
            return False, f"Order type {order_type} is not allowed for AI execution", {}

        # 6. Max Order Value Limit
        order_val = price * Decimal(str(quantity))
        if order_val > perm.max_order_value:
            return False, f"AI Order value ₹{order_val:,.2f} exceeds user limit ₹{perm.max_order_value:,.2f}", {}

        # 7. Auto-Sell Position Verification (Strict oversell prevention)
        if action == "SELL":
            port_res = await db.execute(select(Portfolio).where(Portfolio.user_id == user_id))
            portfolio = port_res.scalar_one_or_none()
            owned_qty = 0
            if portfolio:
                pos_res = await db.execute(
                    select(PortfolioPosition)
                    .where(PortfolioPosition.portfolio_id == portfolio.id)
                    .where(PortfolioPosition.symbol == symbol)
                    .where(PortfolioPosition.is_active == True)
                )
                pos = pos_res.scalar_one_or_none()
                if pos:
                    owned_qty = pos.quantity

            if owned_qty < quantity:
                return False, f"AI Auto-Sell blocked: Owned quantity {owned_qty} < Signal quantity {quantity}", {}

        # Permission check passed
        await log_audit_event(
            db=db,
            action="AI_AUTO_TRADE_ALLOWED",
            user_id=user_id,
            resource_type="ai_signal",
            resource_id=symbol,
            details={"action": action, "quantity": quantity, "price": float(price)}
        )

        return True, "AI Trading Permission validated successfully", {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": float(price),
            "order_type": order_type,
            "stop_loss": float(signal.get("stop_loss", 0.0)) if signal.get("stop_loss") else None,
            "target": float(signal.get("target", 0.0)) if signal.get("target") else None,
            "strategy": signal.get("strategy", "GENAI_MOMENTUM")
        }
