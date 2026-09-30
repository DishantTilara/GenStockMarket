import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.providers.broker.base import BrokerProvider


class PaperBrokerProvider(BrokerProvider):
    """Simulated paper trading broker engine ensuring realistic execution with transparent labels."""

    def __init__(self):
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._positions: Dict[str, Dict[str, Any]] = {}

    async def connect(self) -> bool:
        return True

    async def get_account(self) -> Dict[str, Any]:
        return {
            "broker": "PAPER_TRADING_SIMULATOR",
            "account_id": "PAPER-DEMO-999",
            "status": "ACTIVE",
            "type": "SIMULATED",
            "margin_available": 1000000.00
        }

    async def get_positions(self) -> List[Dict[str, Any]]:
        return list(self._positions.values())

    async def get_orders(self) -> List[Dict[str, Any]]:
        return list(self._orders.values())

    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        order_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        placed_order = {
            "order_id": order_id,
            "mode": "SIMULATED_PAPER_TRADE",
            "symbol": order_data["symbol"],
            "side": order_data["side"],
            "quantity": order_data["quantity"],
            "price": order_data["price"],
            "status": "FILLED",
            "fill_price": order_data["price"],
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
        self._orders[order_id] = placed_order
        return placed_order

    async def modify_order(self, order_id: str, modification_data: Dict[str, Any]) -> Dict[str, Any]:
        if order_id not in self._orders:
            raise ValueError(f"Order {order_id} not found in paper broker")
        self._orders[order_id].update(modification_data)
        return self._orders[order_id]

    async def cancel_order(self, order_id: str) -> bool:
        if order_id in self._orders:
            self._orders[order_id]["status"] = "CANCELLED"
            return True
        return False

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        return self._orders.get(order_id, {"order_id": order_id, "status": "UNKNOWN"})
