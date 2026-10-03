from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class NewsProvider(ABC):
    """Abstract base class for financial news providers."""

    @abstractmethod
    async def get_news(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch normalized market news articles."""
        pass
