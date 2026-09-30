from app.core.config import settings
from app.providers.ai.base import LLMProvider
from app.providers.ai.openai_provider import OpenAIProvider
from app.providers.ai.local_provider import LocalLLMProvider

_instance: LLMProvider = None


def get_llm_provider() -> LLMProvider:
    global _instance
    if _instance is None:
        provider_name = settings.LLM_PROVIDER.lower()
        if provider_name == "local":
            _instance = LocalLLMProvider()
        else:
            _instance = OpenAIProvider()
    return _instance
