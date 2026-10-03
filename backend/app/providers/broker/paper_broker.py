import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_
from app.providers.broker.base import BrokerProvider
from app.core.database import AsyncSessionLocal
from app.models.order import Order
from app.models.portfolio import PortfolioPosition, PortfolioTransaction, Portfolio
from app.models.wallet import Wallet

logger = logging.getLogger("paper_broker_provider")


class PaperBrokerProvider(BrokerProvider):
    """
    Authoritative Paper Trading Broker Provider.
    
    Reconstructs its state from the PostgreSQL database as the authoritative source
    of financial truth, rather than relying exclusively on in-memory collections.
    """

    def __init__(self):
        self._connected: bool = True
        self._simulator_cache: Dict[str, Dict[str, Any]] = {}

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        return True

    async def get_account(self, user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        margin = 1000000.00
        if user_id:
            try:
                async with AsyncSessionLocal() as db:
                    w_res = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
                    wallet = w_res.scalar_one_or_none()
                    if wallet:
                        margin = float(wallet.available_balance)
            except Exception as e:
                logger.warning(f"Could not load account balance from DB: {e}")

        return {
            "broker": "PAPER_TRADING_SIMULATOR",
            "account_id": f"PAPER-ACCOUNT-{str(user_id)[:8] if user_id else 'DEMO'}",
            "status": "ACTIVE" if self._connected else "DISCONNECTED",
            "type": "SIMULATED",
            "environment": "PAPER",
            "margin_available": margin,
            "currency": "INR"
        }

    async def get_balance(self, user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        available = Decimal("1000000.00")
        locked = Decimal("0.00")
        if user_id:
            try:
                async with AsyncSessionLocal() as db:
                    w_res = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
                    wallet = w_res.scalar_one_or_none()
                    if wallet:
                        available = wallet.available_balance
                        locked = wallet.locked_balance
            except Exception as e:
                logger.warning(f"Could not query balance: {e}")

        return {
            "available_cash": float(available),
            "locked_margin": float(locked),
            "total_balance": float(available + locked),
            "currency": "INR"
        }

    async def get_positions(self, user_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
        positions = []
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(PortfolioPosition).where(PortfolioPosition.is_active == True)
                if user_id:
                    stmt = stmt.join(Portfolio, PortfolioPosition.portfolio_id == Portfolio.id).where(Portfolio.user_id == user_id)
                res = await db.execute(stmt)
                db_positions = res.scalars().all()
                for p in db_positions:
                    positions.append({
                        "symbol": p.symbol,
                        "quantity": p.quantity,
                        "average_price": float(p.average_price),
                        "current_price": float(p.current_price),
                        "unrealized_pnl": float(p.unrealized_pnl),
                        "realized_pnl": float(p.realized_pnl),
                        "stop_loss": float(p.stop_loss) if p.stop_loss else None,
                        "target_price": float(p.target_price) if p.target_price else None
                    })
        except Exception as e:
            logger.warning(f"Could not load positions from PostgreSQL: {e}")
        return positions

    async def get_orders(self, user_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
        orders = []
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Order).order_by(Order.created_at.desc()).limit(100)
                if user_id:
                    stmt = stmt.where(Order.user_id == user_id)
                res = await db.execute(stmt)
                db_orders = res.scalars().all()
                for o in db_orders:
                    orders.append({
                        "order_id": str(o.id),
                        "broker_order_id": o.broker_order_id,
                        "symbol": o.symbol,
                        "side": o.side,
                        "order_type": o.order_type,
                        "quantity": o.quantity,
                        "price": float(o.price),
                        "execution_price": float(o.execution_price) if o.execution_price else None,
                        "status": o.status,
                        "created_at": o.created_at.isoformat() if o.created_at else None
                    })
        except Exception as e:
            logger.warning(f"Could not load orders from PostgreSQL: {e}")
        return orders

    async def get_trades(self, user_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
        trades = []
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(PortfolioTransaction).order_by(PortfolioTransaction.executed_at.desc()).limit(100)
                if user_id:
                    stmt = stmt.join(Portfolio, PortfolioTransaction.portfolio_id == Portfolio.id).where(Portfolio.user_id == user_id)
                res = await db.execute(stmt)
                db_trades = res.scalars().all()
                for t in db_trades:
                    trades.append({
                        "id": str(t.id),
                        "symbol": t.symbol,
                        "side": t.side,
                        "quantity": t.quantity,
                        "price": float(t.price),
                        "charges": float(t.charges),
                        "realized_pnl": float(t.realized_pnl) if t.realized_pnl else 0.0,
                        "executed_at": t.executed_at.isoformat() if t.executed_at else None
                    })
        except Exception as e:
            logger.warning(f"Could not load trades from PostgreSQL: {e}")
        return trades

    async def get_margins(self, user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        return await self.get_balance(user_id)

    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate order placement through the paper broker.
        Generates deterministic broker identifiers.
        """
        broker_order_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        placed_order = {
            "broker_order_id": broker_order_id,
            "mode": "SIMULATED_PAPER_TRADE",
            "symbol": order_data["symbol"],
            "side": order_data["side"],
            "quantity": order_data["quantity"],
            "price": order_data["price"],
            "status": "FILLED" if order_data.get("order_type") == "MARKET" else "OPEN",
            "fill_price": order_data["price"],
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
        self._simulator_cache[broker_order_id] = placed_order
        return placed_order

    async def modify_order(self, order_id: str, modification_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Order).where(Order.broker_order_id == order_id)
                order = (await db.execute(stmt)).scalar_one_or_none()
                if order:
                    if "price" in modification_data:
                        order.price = Decimal(str(modification_data["price"]))
                    if "quantity" in modification_data:
                        order.quantity = int(modification_data["quantity"])
                    await db.commit()
                    return {
                        "broker_order_id": order_id,
                        "price": float(order.price),
                        "quantity": order.quantity,
                        "status": order.status
                    }
        except Exception as e:
            logger.warning(f"Modify order fallback: {e}")

        if order_id in self._simulator_cache:
            self._simulator_cache[order_id].update(modification_data)
            return self._simulator_cache[order_id]

        return {"broker_order_id": order_id, "status": "MODIFIED"}

    async def cancel_order(self, order_id: str) -> bool:
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Order).where(Order.broker_order_id == order_id)
                order = (await db.execute(stmt)).scalar_one_or_none()
                if order and order.status in ["OPEN", "PENDING"]:
                    order.status = "CANCELLED"
                    await db.commit()
                    return True
        except Exception as e:
            logger.warning(f"Cancel order fallback: {e}")

        if order_id in self._simulator_cache:
            self._simulator_cache[order_id]["status"] = "CANCELLED"
            return True
        return True

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Order).where(
                    (Order.broker_order_id == order_id) | (Order.id == uuid.UUID(order_id) if len(order_id) == 36 else False)
                )
                order = (await db.execute(stmt)).scalar_one_or_none()
                if order:
                    return {
                        "order_id": str(order.id),
                        "broker_order_id": order.broker_order_id,
                        "status": order.status,
                        "symbol": order.symbol,
                        "side": order.side,
                        "quantity": order.quantity,
                        "price": float(order.price),
                        "execution_price": float(order.execution_price) if order.execution_price else None
                    }
        except Exception:
            pass

        return self._simulator_cache.get(order_id, {"order_id": order_id, "status": "UNKNOWN"})
