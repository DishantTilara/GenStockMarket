import logging
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings
from app.providers.news.provider import NewsProvider
from app.providers.news.simulated_provider import SimulatedNewsProvider

logger = logging.getLogger(__name__)


def _estimate_sentiment(text: str) -> Dict[str, Any]:
    """Basic keyword-driven sentiment analysis for financial headlines."""
    lower = text.lower()
    bullish_keywords = ["growth", "profit", "gain", "rally", "expands", "record", "surge", "positive", "high", "dividend", "bonus"]
    bearish_keywords = ["drop", "fall", "loss", "plunge", "decline", "cut", "weak", "slump", "down", "debt", "inflation"]

    bull_count = sum(1 for w in bullish_keywords if w in lower)
    bear_count = sum(1 for w in bearish_keywords if w in lower)

    if bull_count > bear_count:
        return {"sentiment": "BULLISH", "sentiment_score": 0.75}
    elif bear_count > bull_count:
        return {"sentiment": "BEARISH", "sentiment_score": -0.75}
    return {"sentiment": "NEUTRAL", "sentiment_score": 0.0}


class NewsApiProvider(NewsProvider):
    """
    Live NewsAPI provider with seamless fallback to SimulatedNewsProvider
    when the API key is not supplied, expired, or rate-limited.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.NEWS_API_KEY
        self.fallback = SimulatedNewsProvider()
        self.base_url = "https://newsapi.org/v2"

    async def get_news(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.api_key or self.api_key.startswith("YOUR_"):
            return await self.fallback.get_news(symbol, limit)

        query = f"({symbol} OR Indian stock market OR NSE OR BSE)" if symbol else "(Indian stock market OR Sensex OR Nifty 50 OR RBI)"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": min(limit, 50),
                    "apiKey": self.api_key,
                }
                resp = await client.get(f"{self.base_url}/everything", params=params)

                if resp.status_code != 200:
                    logger.warning(f"NewsAPI returned status {resp.status_code}: {resp.text}. Falling back to simulated news.")
                    return await self.fallback.get_news(symbol, limit)

                data = resp.json()
                raw_articles = data.get("articles", [])
                if not raw_articles:
                    return await self.fallback.get_news(symbol, limit)

                results = []
                for art in raw_articles[:limit]:
                    title = art.get("title") or "Market Update"
                    content = art.get("description") or art.get("content") or title
                    sent = _estimate_sentiment(title + " " + content)

                    results.append({
                        "title": title,
                        "source": (art.get("source") or {}).get("name") or "NewsAPI",
                        "url": art.get("url"),
                        "symbol": symbol.upper() if symbol else "MARKET",
                        "content": content,
                        "sentiment": sent["sentiment"],
                        "sentiment_score": sent["sentiment_score"],
                        "published_at": art.get("publishedAt") or "",
                    })
                return results

        except Exception as exc:
            logger.warning(f"Error querying NewsAPI: {exc}. Falling back to simulated news.")
            return await self.fallback.get_news(symbol, limit)
