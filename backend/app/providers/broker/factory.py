from app.core.config import settings
from app.providers.broker.base import BrokerProvider
from app.providers.broker.paper_broker import PaperBrokerProvider
from app.providers.broker.sandbox_broker import SandboxBrokerProvider
from app.providers.broker.live_broker import LiveBrokerProvider

_instance: BrokerProvider = None


def get_broker_provider(provider_type: str = None) -> BrokerProvider:
    global _instance
    if provider_type:
        target = provider_type.lower()
    else:
        if settings.TRADING_MODE == "SANDBOX" or settings.BROKER_PROVIDER.lower() == "sandbox":
            target = "sandbox"
        elif settings.TRADING_MODE == "LIVE":
            target = "live"
        else:
            target = "paper"

    if _instance is None or getattr(_instance, "_provider_key", None) != target:
        if target == "sandbox":
            _instance = SandboxBrokerProvider()
            _instance._provider_key = "sandbox"
        elif target == "live":
            _instance = LiveBrokerProvider()
            _instance._provider_key = "live"
        else:
            _instance = PaperBrokerProvider()
            _instance._provider_key = "paper"

    return _instance


def reset_broker_provider():
    global _instance
    _instance = None

