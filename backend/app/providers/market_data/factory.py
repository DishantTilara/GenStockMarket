from app.core.config import settings
from app.providers.market_data.base import MarketDataProvider
from app.providers.market_data.simulated_provider import SimulatedMarketDataProvider

_instance: MarketDataProvider = None


def get_market_data_provider() -> MarketDataProvider:
    global _instance
    if _instance is None:
        provider_name = settings.MARKET_DATA_PROVIDER.lower()
        if provider_name == "simulated":
            _instance = SimulatedMarketDataProvider()
        else:
            # Future real provider integration (e.g. KiteConnect / AngelOne)
            _instance = SimulatedMarketDataProvider()
    return _instance
