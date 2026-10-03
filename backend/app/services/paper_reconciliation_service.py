import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.config import settings
from app.models.wallet import Wallet, LedgerEntry
from app.models.order import Order
from app.models.portfolio import Portfolio, PortfolioPosition, PortfolioTransaction

logger = logging.getLogger("paper_reconciliation")


class PaperReconciliationService:
    @classmethod
    async def reconcile_paper_trading(cls, db: AsyncSession) -> Dict[str, Any]:
        """Audits consistency between paper wallets, ledger entries, orders, and positions."""
        # 1. Count open orders
        open_orders_res = await db.execute(
            select(func.count(Order.id)).where(Order.status == "PENDING")
        )
        open_orders_count = open_orders_res.scalar() or 0

        # 2. Count active open positions
        open_positions_res = await db.execute(
            select(func.count(PortfolioPosition.id))
            .where(and_(PortfolioPosition.quantity > 0, PortfolioPosition.is_active == True))
        )
        open_positions_count = open_positions_res.scalar() or 0

        # 3. Check wallet consistency (available >= 0, locked >= 0)
        wallets_res = await db.execute(select(Wallet))
        wallets = wallets_res.scalars().all()
        wallet_consistent = True
        for w in wallets:
            if Decimal(str(w.available_balance)) < Decimal("0.00") or Decimal(str(w.locked_balance)) < Decimal("0.00"):
                wallet_consistent = False
                logger.warning(f"Inconsistent wallet {w.id}: available={w.available_balance}, locked={w.locked_balance}")
                break

        # 4. Check portfolio consistency (no negative position quantities)
        positions_res = await db.execute(select(PortfolioPosition))
        positions = positions_res.scalars().all()
        portfolio_consistent = True
        for p in positions:
            if p.quantity < 0 or Decimal(str(p.average_price)) < Decimal("0.00"):
                portfolio_consistent = False
                logger.warning(f"Inconsistent position {p.id} for {p.symbol}: qty={p.quantity}")
                break

        status = "HEALTHY" if (wallet_consistent and portfolio_consistent) else "DEGRADED"

        return {
            "mode": settings.TRADING_MODE,
            "status": status,
            "open_orders": open_orders_count,
            "open_positions": open_positions_count,
            "wallet_consistent": wallet_consistent,
            "portfolio_consistent": portfolio_consistent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
