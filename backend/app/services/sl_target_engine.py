import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.portfolio import Portfolio, PortfolioPosition
from app.models.order import Order
from app.services.order_state_machine import OrderStateMachine
from app.core.audit import log_audit_event

logger = logging.getLogger("sl_target_engine")


class SLTargetEngine:
    """
    Deterministic Stop-Loss & Target Monitoring Engine.
    Monitors market ticks against open positions and orders without LLM dependency.
    """

    @classmethod
    async def evaluate_tick_triggers(
        cls,
        db: AsyncSession,
        symbol: str,
        current_price: Decimal
    ) -> List[Dict[str, Any]]:
        triggers: List[Dict[str, Any]] = []

        # Find open positions for this symbol that have SL or Target set
        stmt = (
            select(PortfolioPosition)
            .where(PortfolioPosition.symbol == symbol.upper())
            .where(PortfolioPosition.is_active == True)
        )
        res = await db.execute(stmt)
        positions = res.scalars().all()

        for pos in positions:
            # Query the entry order for stop_loss and target
            order_res = await db.execute(
                select(Order)
                .where(Order.portfolio_id == pos.portfolio_id)
                .where(Order.symbol == symbol.upper())
                .where(Order.status == OrderStateMachine.FILLED)
                .order_by(Order.created_at.desc())
            )
            order = order_res.scalars().first()
            if not order:
                continue

            sl = order.stop_loss
            tgt = order.target

            # Stop loss trigger (for long BUY position)
            if sl and current_price <= sl:
                triggers.append({
                    "type": "STOP_LOSS_TRIGGERED",
                    "symbol": symbol.upper(),
                    "position_id": str(pos.id),
                    "quantity": pos.quantity,
                    "trigger_price": float(current_price),
                    "stop_loss_level": float(sl)
                })
                logger.warning(f"[SL ENGINE] Stop loss triggered for {symbol}: price {current_price} <= {sl}")

            # Target price trigger
            elif tgt and current_price >= tgt:
                triggers.append({
                    "type": "TARGET_PROFIT_TRIGGERED",
                    "symbol": symbol.upper(),
                    "position_id": str(pos.id),
                    "quantity": pos.quantity,
                    "trigger_price": float(current_price),
                    "target_level": float(tgt)
                })
                logger.info(f"[TARGET ENGINE] Target achieved for {symbol}: price {current_price} >= {tgt}")

        return triggers
