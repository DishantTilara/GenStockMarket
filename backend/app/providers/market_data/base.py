from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Any, Optional


class MarketDataProvider(ABC):
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection with the market data feed."""
        pass

    @abstractmethod
    async def stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Continuous generator yielding live tick or snapshot dicts."""
        if False:
            yield {}

    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Retrieve latest L1 quote snapshot for symbol."""
        pass

    @abstractmethod
    async def get_minute_bars(self, symbol: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Retrieve 1-minute historical candlestick bars."""
        pass

    @abstractmethod
    async def get_historical_data(self, symbol: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Retrieve historical daily bars."""
        pass

    async def get_history(self, symbol: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Alias for get_historical_data."""
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)
        if not end:
            end = now
        if not start:
            start = end - timedelta(days=90)
        return await self.get_historical_data(symbol, start, end)

    @abstractmethod
    async def get_instruments(self) -> List[Dict[str, Any]]:
        """Retrieve active Indian instruments catalog."""
        pass

    @abstractmethod
    async def market_status(self) -> Dict[str, Any]:
        """Retrieve current exchange trading session status."""
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Retrieve health and connectivity status of market data feed."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Terminate connection gracefully."""
        pass

    async def disconnect(self) -> None:
        """Alias for close()."""
        await self.close()
