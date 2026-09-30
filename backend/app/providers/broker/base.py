from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BrokerProvider(ABC):
    @abstractmethod
    async def connect(self) -> bool:
        pass

    @abstractmethod
    async def get_account(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_orders(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def modify_order(self, order_id: str, modification_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        pass
