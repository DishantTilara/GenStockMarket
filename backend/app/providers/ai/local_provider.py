import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.providers.ai.base import LLMProvider
from app.providers.ai.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class LocalLLMProvider(LLMProvider):
    """Local LLM provider interfacing with Ollama or local vLLM instances."""

    def __init__(self):
        self.url = settings.LOCAL_LLM_URL
        self.fallback = OpenAIProvider()
        self.client = httpx.AsyncClient(timeout=45.0)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        try:
            payload = {
                "model": "llama3.1",
                "messages": messages,
                "stream": False
            }
            resp = await self.client.post(f"{self.url}/chat/completions", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {"content": content, "tool_calls": []}
        except Exception:
            pass

        # Fallback to grounded deterministic agent
        return await self.fallback.chat(messages, tools, temperature)

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return await self.fallback.generate_structured(prompt, system_prompt, schema)
