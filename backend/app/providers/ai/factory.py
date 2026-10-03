from typing import Optional
from app.core.config import settings
from app.providers.ai.base import LLMProvider
from app.providers.ai.groq_provider import GroqProvider
from app.providers.ai.openai_provider import OpenAIProvider
from app.providers.ai.local_provider import LocalLLMProvider

_instance: Optional[LLMProvider] = None


def get_llm_provider(force_refresh: bool = False) -> LLMProvider:
    global _instance
    if _instance is None or force_refresh:
        provider_name = (
            getattr(settings, "LLM_PROVIDER", None)
            or getattr(settings, "AI_PROVIDER", None)
            or "groq"
        ).lower().strip()
        if provider_name == "openai":
            _instance = OpenAIProvider()
        elif provider_name == "local":
            _instance = LocalLLMProvider()
        else:
            _instance = GroqProvider()
    return _instance
