from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Send chat messages and optional tool definitions to the LLM."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate verified structured JSON output adhering to schema."""
        pass
