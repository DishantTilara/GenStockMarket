import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.providers.news.simulated_provider import SimulatedNewsProvider
from app.providers.news.newsapi_provider import NewsApiProvider, _estimate_sentiment
from app.providers.news.factory import get_news_provider


def test_sentiment_estimation():
    assert _estimate_sentiment("Company reports record high profit growth")["sentiment"] == "BULLISH"
    assert _estimate_sentiment("Market faces heavy drop and loss amid inflation")["sentiment"] == "BEARISH"
    assert _estimate_sentiment("Quarterly earnings meeting scheduled")["sentiment"] == "NEUTRAL"


@pytest.mark.asyncio
async def test_simulated_news_provider():
    provider = SimulatedNewsProvider()
    articles = await provider.get_news(limit=5)
    assert len(articles) > 0
    first = articles[0]
    assert "title" in first
    assert "source" in first
    assert "sentiment" in first
    assert "content" in first


@pytest.mark.asyncio
async def test_newsapi_provider_fallback_when_no_key():
    # When API key is None or placeholder, falls back to simulated news
    provider = NewsApiProvider(api_key=None)
    articles = await provider.get_news("RELIANCE", limit=3)
    assert len(articles) > 0
    assert any("RELIANCE" in a["symbol"] or "RELIANCE" in a["title"] for a in articles)


@pytest.mark.asyncio
async def test_news_factory_selection():
    with patch("app.core.config.settings.NEWS_PROVIDER", "simulated"):
        prov = get_news_provider()
        assert isinstance(prov, SimulatedNewsProvider)

    with patch("app.core.config.settings.NEWS_PROVIDER", "newsapi"):
        prov = get_news_provider()
        assert isinstance(prov, NewsApiProvider)


@pytest.mark.asyncio
async def test_news_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/news")
        assert resp.status_code == 200
        articles = resp.json()
        assert isinstance(articles, list)
        assert len(articles) > 0
        assert "title" in articles[0]
