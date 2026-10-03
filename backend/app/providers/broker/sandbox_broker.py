import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from app.providers.broker.base import BrokerProvider
from app.core.config import settings

logger = logging.getLogger("sandbox_broker")


class SandboxBrokerProvider(BrokerProvider):
    """
    Sandbox Broker Provider.
    Implements BrokerProvider interface for the SANDBOX environment.
    Simulates realistic broker environment:
    - Broker connectivity & handshake
    - Margin calculations and balance check
    - Broker order submission with broker_order_id
    - Immediate / partial simulated fills
    - Order cancellation and modification
    - Trade logs & broker positions
    """

    def __init__(self, api_key: Optional[str] = None, client_id: Optional[str] = None):
        self.api_key = api_key or settings.BROKER_API_KEY or "sandbox_test_key"
        self.client_id = client_id or "SANDBOX_CLIENT_001"
        self._connected = False
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._trades: List[Dict[str, Any]] = []
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._cash_balance = Decimal("2000000.00")  # ₹20 Lakhs virtual sandbox capital

    async def connect(self) -> bool:
        if settings.TRADING_MODE not in ["SANDBOX", "PAPER"] and settings.APP_ENV not in ["development", "test"]:
            logger.error("SandboxBrokerProvider cannot connect in non-sandbox/test trading mode")
            return False
        self._connected = True
        logger.info(f"[SANDBOX BROKER] Connected successfully with client {self.client_id}")
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        logger.info(f"[SANDBOX BROKER] Disconnected client {self.client_id}")
        return True

    async def get_account(self) -> Dict[str, Any]:
        return {
            "broker_name": "SANDBOX_GATEWAY",
            "environment": "SANDBOX",
            "client_id": self.client_id,
            "account_status": "ACTIVE" if self._connected else "DISCONNECTED",
            "account_type": "EQUITY_DERIVATIVES",
            "exchanges": ["NSE", "BSE"],
            "currency": "INR",
            "is_connected": self._connected
        }

    async def get_balance(self) -> Dict[str, Any]:
        used_margin = sum(
            Decimal(str(p["quantity"])) * Decimal(str(p["average_price"]))
            for p in self._positions.values()
        )
        return {
            "cash_balance": float(self._cash_balance),
            "available_margin": float(self._cash_balance),
            "used_margin": float(used_margin),
            "collateral": 0.0,
            "currency": "INR"
        }

    async def get_margins(self) -> Dict[str, Any]:
        return await self.get_balance()

    async def get_positions(self) -> List[Dict[str, Any]]:
        return list(self._positions.values())

    async def get_orders(self) -> List[Dict[str, Any]]:
        return list(self._orders.values())

    async def get_trades(self) -> List[Dict[str, Any]]:
        return self._trades

    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = order_data["symbol"].upper()
        side = order_data["side"].upper()
        qty = int(order_data["quantity"])
        order_type = order_data.get("order_type", "LIMIT").upper()
        price = Decimal(str(order_data.get("price", 0.0)))

        broker_order_id = f"SBX-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        # Sandbox reject conditions (for error testing)
        if symbol == "REJECT_ME":
            return {
                "broker_order_id": broker_order_id,
                "status": "REJECTED",
                "reason": "Broker simulated rejection for symbol REJECT_ME"
            }

        # Simulated fill
        exec_price = price if price > Decimal("0.00") else Decimal("1000.00")
        total_val = exec_price * Decimal(str(qty))

        order_record = {
            "broker_order_id": broker_order_id,
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": qty,
            "price": float(price),
            "status": "FILLED",
            "filled_quantity": qty,
            "average_price": float(exec_price),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._orders[broker_order_id] = order_record

        # Generate broker trade
        trade_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"
        trade_record = {
            "broker_trade_id": trade_id,
            "broker_order_id": broker_order_id,
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "price": float(exec_price),
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
        self._trades.append(trade_record)

        # Update position
        if side == "BUY":
            if symbol in self._positions:
                cur = self._positions[symbol]
                old_qty = cur["quantity"]
                old_avg = Decimal(str(cur["average_price"]))
                new_qty = old_qty + qty
                new_avg = ((old_avg * Decimal(str(old_qty))) + (exec_price * Decimal(str(qty)))) / Decimal(str(new_qty))
                cur["quantity"] = new_qty
                cur["average_price"] = float(round(new_avg, 2))
            else:
                self._positions[symbol] = {
                    "symbol": symbol,
                    "quantity": qty,
                    "average_price": float(exec_price),
                    "pnl": 0.0
                }
            self._cash_balance -= total_val
        elif side == "SELL":
            if symbol in self._positions:
                cur = self._positions[symbol]
                cur["quantity"] = max(0, cur["quantity"] - qty)
                if cur["quantity"] == 0:
                    del self._positions[symbol]
            self._cash_balance += total_val

        return order_record

    async def modify_order(self, order_id: str, modification_data: Dict[str, Any]) -> Dict[str, Any]:
        if order_id not in self._orders:
            raise LookupError(f"Broker order {order_id} not found in sandbox")
        order = self._orders[order_id]
        if order["status"] == "FILLED":
            return {"status": "REJECTED", "reason": "Cannot modify completely filled order"}
        if "quantity" in modification_data:
            order["quantity"] = int(modification_data["quantity"])
        if "price" in modification_data:
            order["price"] = float(modification_data["price"])
        return order

    async def cancel_order(self, order_id: str) -> bool:
        if order_id not in self._orders:
            return False
        order = self._orders[order_id]
        if order["status"] == "FILLED":
            return False
        order["status"] = "CANCELLED"
        return True

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        if order_id not in self._orders:
            return {"status": "UNKNOWN", "broker_order_id": order_id}
        return self._orders[order_id]
