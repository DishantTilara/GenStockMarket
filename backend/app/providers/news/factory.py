from app.core.config import settings
from app.providers.news.provider import NewsProvider
from app.providers.news.simulated_provider import SimulatedNewsProvider
from app.providers.news.newsapi_provider import NewsApiProvider


def get_news_provider() -> NewsProvider:
    """Factory to retrieve configured news provider."""
    provider_name = getattr(settings, "NEWS_PROVIDER", "simulated").lower()
    if provider_name == "newsapi":
        return NewsApiProvider()
    return SimulatedNewsProvider()
