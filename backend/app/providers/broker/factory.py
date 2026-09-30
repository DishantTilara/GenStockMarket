from app.core.config import settings
from app.providers.broker.base import BrokerProvider
from app.providers.broker.paper_broker import PaperBrokerProvider

_instance: BrokerProvider = None


def get_broker_provider() -> BrokerProvider:
    global _instance
    if _instance is None:
        _instance = PaperBrokerProvider()
    return _instance
