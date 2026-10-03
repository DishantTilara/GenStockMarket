from typing import Optional
from app.core.config import settings
from app.providers.market_data.base import MarketDataProvider
from app.providers.market_data.simulated_provider import SimulatedMarketDataProvider
from app.providers.market_data.yfinance_provider import YFinanceMarketDataProvider
from app.providers.market_data.production_realtime_provider import ProductionRealtimeMarketProvider

_instance: Optional[MarketDataProvider] = None


def get_market_data_provider(force_refresh: bool = False) -> MarketDataProvider:
    global _instance
    if _instance is None or force_refresh:
        provider_name = (settings.MARKET_DATA_PROVIDER or "yfinance").lower().strip()
        if provider_name == "simulated":
            _instance = SimulatedMarketDataProvider()
        elif provider_name in ["production", "realtime"]:
            _instance = ProductionRealtimeMarketProvider(
                api_key=settings.MARKET_DATA_API_KEY,
                api_secret=settings.MARKET_DATA_API_SECRET
            )
        else:
            _instance = YFinanceMarketDataProvider()
    return _instance


def set_market_data_provider(provider: Optional[MarketDataProvider]) -> None:
    global _instance
    _instance = provider


