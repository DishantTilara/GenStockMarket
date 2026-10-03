import json
import os
import re
from unittest.mock import patch, AsyncMock
import httpx
import pytest

from app.core.config import settings
from app.providers.ai.factory import get_llm_provider
from app.providers.ai.groq_provider import (
    GroqProvider,
    GroqConfigurationError,
    GroqAuthenticationError,
    GroqRateLimitError,
    GroqTimeoutError,
    GroqAPIError,
    mask_api_key,
    sanitize_message,
)


@pytest.mark.asyncio
async def test_groq_provider_initialization():
    """1. Groq provider initialization."""
    provider = GroqProvider(api_key="test-key", model="llama-3.3-70b-versatile")
    assert provider.api_key == "test-key"
    assert provider.model == "llama-3.3-70b-versatile"
    assert "groq.com" in provider.base_url
    assert provider.timeout > 0
    await provider.close()


@pytest.mark.asyncio
async def test_groq_provider_missing_api_key():
    """2. Missing API key handling."""
    # Ensure without API key, chat returns a safe message or raises if raise_on_error=True
    provider = GroqProvider(api_key="")
    
    # Safe return mode (default)
    res = await provider.chat([{"role": "user", "content": "What is the market status?"}])
    assert "Groq API configuration is missing." in res["content"]
    assert res.get("error") == "Groq API configuration is missing."
    assert res["tool_calls"] == []
    
    # Raise mode
    with pytest.raises(GroqConfigurationError) as exc_info:
        await provider.chat([{"role": "user", "content": "Hello"}], raise_on_error=True)
    assert "Groq API configuration is missing." in str(exc_info.value)
    
    await provider.close()


@pytest.mark.asyncio
async def test_groq_provider_valid_configuration():
    """3. Valid configuration."""
    provider = GroqProvider(
        api_key="test-key-12345",
        model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
        timeout=45.0
    )
    assert provider.api_key == "test-key-12345"
    assert provider.model == "llama-3.3-70b-versatile"
    assert provider.base_url == "https://api.groq.com/openai/v1"
    assert provider.timeout == 45.0
    await provider.close()


@pytest.mark.asyncio
async def test_groq_provider_model_configuration():
    """4. Model configuration flexibility."""
    # Test custom model
    provider = GroqProvider(api_key="test-key", model="mixtral-8x7b-32768")
    assert provider.model == "mixtral-8x7b-32768"
    await provider.close()

    # Test default fallback model
    provider_default = GroqProvider(api_key="test-key")
    assert provider_default.model == settings.GROQ_MODEL
    assert "llama" in provider_default.model
    await provider_default.close()


@pytest.mark.asyncio
async def test_groq_provider_successful_response():
    """5. Successful Groq response."""
    provider = GroqProvider(api_key="test-valid-key", model="llama-3.3-70b-versatile")

    mock_resp = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Indian equities show constructive momentum with NIFTY 50 trading above 25,000."
                }
            }
        ]
    }

    mock_http_response = httpx.Response(
        status_code=200,
        json=mock_resp,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    )

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_http_response
        result = await provider.chat([{"role": "user", "content": "How is NIFTY looking today?"}])

        assert "constructive momentum" in result["content"]
        assert result["tool_calls"] == []
        mock_post.assert_called_once()

    await provider.close()


@pytest.mark.asyncio
async def test_groq_provider_tool_calls_execution():
    """5b. Test tool calling execution through Groq provider."""
    provider = GroqProvider(api_key="test-valid-key", model="llama-3.3-70b-versatile")

    # Step 1: Model calls a tool
    mock_tool_call_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "get_market_status",
                                "arguments": "{}"
                            }
                        }
                    ]
                }
            }
        ]
    }

    # Step 2: Model synthesizes result
    mock_synthesis_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "The market is currently OPEN and trading normally."
                }
            }
        ]
    }

    resp1 = httpx.Response(status_code=200, json=mock_tool_call_response, request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"))
    resp2 = httpx.Response(status_code=200, json=mock_synthesis_response, request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"))

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [resp1, resp2]
        result = await provider.chat([{"role": "user", "content": "Check market status"}])

        assert "trading normally" in result["content"]
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "get_market_status"
        assert mock_post.call_count == 2

    await provider.close()


@pytest.mark.asyncio
async def test_groq_provider_api_error_handling():
    """6. API error handling (401 Invalid Key, 500 Internal Server Error, Malformed JSON)."""
    provider = GroqProvider(api_key="invalid-key")

    # 401 Unauthorized
    resp_401 = httpx.Response(
        status_code=401,
        json={"error": {"message": "Invalid API key"}},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    )
    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp_401
        res = await provider.chat([{"role": "user", "content": "Hello"}])
        assert "authentication failed" in res["content"].lower()
        assert "invalid-key" not in res["content"]

        with pytest.raises(GroqAuthenticationError):
            await provider.chat([{"role": "user", "content": "Hello"}], raise_on_error=True)

    # 500 Server Error
    resp_500 = httpx.Response(
        status_code=500,
        text="Internal Server Error",
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    )
    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp_500
        res = await provider.chat([{"role": "user", "content": "Hello"}])
        assert "unavailable" in res["content"].lower() or "error" in res["content"].lower()

    # Malformed JSON
    resp_malformed = httpx.Response(
        status_code=200,
        text="not json at all",
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    )
    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp_malformed
        res = await provider.chat([{"role": "user", "content": "Hello"}])
        assert "malformed" in res["content"].lower()

    await provider.close()


@pytest.mark.asyncio
async def test_groq_provider_rate_limit_handling():
    """7. Rate-limit handling (429 Too Many Requests)."""
    provider = GroqProvider(api_key="test-key")

    resp_429 = httpx.Response(
        status_code=429,
        json={"error": {"message": "Rate limit reached"}},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    )

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp_429
        res = await provider.chat([{"role": "user", "content": "Hello"}])
        assert "rate limit" in res["content"].lower()

        with pytest.raises(GroqRateLimitError):
            await provider.chat([{"role": "user", "content": "Hello"}], raise_on_error=True)

    await provider.close()


@pytest.mark.asyncio
async def test_groq_provider_timeout_handling():
    """8. Timeout handling."""
    provider = GroqProvider(api_key="test-key")

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")
        res = await provider.chat([{"role": "user", "content": "Hello"}])
        assert "timed out" in res["content"].lower()

        with pytest.raises(GroqTimeoutError):
            await provider.chat([{"role": "user", "content": "Hello"}], raise_on_error=True)

    await provider.close()


@pytest.mark.asyncio
async def test_api_keys_never_returned_by_endpoints(client):
    """9. Confirm that API keys are never returned by API endpoints."""
    # Ensure health or info endpoints do not leak keys
    health_resp = await client.get("/health")
    assert health_resp.status_code == 200
    health_text = health_resp.text
    assert "gsk_" not in health_text
    assert "GROQ_API_KEY" not in health_text

    # Masking test
    fake_key = "gsk_secret1234567890abcdef"
    masked = mask_api_key(fake_key)
    assert masked == "********"
    assert fake_key not in masked

    sanitized = sanitize_message(f"Error calling with {fake_key}", fake_key)
    assert fake_key not in sanitized
    assert "********" in sanitized


def test_frontend_does_not_contain_groq_api_key():
    """10. Confirm frontend does not contain GROQ_API_KEY or leaked secrets."""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend"))
    
    # Check all files in frontend/src
    for root, _, files in os.walk(os.path.join(frontend_dir, "src")):
        for f in files:
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as file_handle:
                content = file_handle.read()
                assert "VITE_GROQ_API_KEY" not in content, f"Leaked key pattern in {path}"
                assert "gsk_" not in content, f"Leaked real key in {path}"
