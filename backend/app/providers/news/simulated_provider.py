from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.providers.news.provider import NewsProvider


class SimulatedNewsProvider(NewsProvider):
    """Simulated Indian equity news provider for offline and testing environments."""

    async def get_news(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        sym = symbol.upper() if symbol else None

        market_news = [
            {
                "title": "RBI Monetary Policy Committee maintains benchmark repo rate at 6.50%",
                "source": "Economic Times",
                "url": "https://economictimes.indiatimes.com/news/economy/policy",
                "symbol": "BANKNIFTY",
                "content": "The Reserve Bank of India Monetary Policy Committee decided unanimously to keep the policy repo rate unchanged at 6.50%. Governor emphasized economic resilience and inflation targeting.",
                "sentiment": "NEUTRAL",
                "sentiment_score": 0.20,
                "published_at": (now - timedelta(hours=2)).isoformat(),
            },
            {
                "title": "Reliance Industries expands new energy gigafactory operations in Jamnagar",
                "source": "LiveMint",
                "url": "https://www.livemint.com/companies/news",
                "symbol": "RELIANCE",
                "content": "Reliance Industries announced key milestone completions for its solar photovoltaic and energy storage manufacturing complex in Jamnagar, Gujarat.",
                "sentiment": "BULLISH",
                "sentiment_score": 0.85,
                "published_at": (now - timedelta(hours=4)).isoformat(),
            },
            {
                "title": "TCS signs $1.2 Billion multi-year enterprise transformation partnership with European insurer",
                "source": "Moneycontrol",
                "url": "https://www.moneycontrol.com/news/business",
                "symbol": "TCS",
                "content": "Tata Consultancy Services secured a mega-deal spanning 8 years to modernize core underwriting systems and cloud infrastructure.",
                "sentiment": "BULLISH",
                "sentiment_score": 0.90,
                "published_at": (now - timedelta(hours=5)).isoformat(),
            },
            {
                "title": "HDFC Bank reports 17% YoY credit growth and stable asset quality in quarterly update",
                "source": "Business Standard",
                "url": "https://www.business-standard.com/finance/banking",
                "symbol": "HDFCBANK",
                "content": "HDFC Bank provisional numbers indicated retail deposits expanded by 18.2% while gross non-performing assets remained steady.",
                "sentiment": "BULLISH",
                "sentiment_score": 0.75,
                "published_at": (now - timedelta(hours=6)).isoformat(),
            },
            {
                "title": "Infosys expands AI generative enterprise suite with global sovereign cloud certifications",
                "source": "Economic Times",
                "url": "https://economictimes.indiatimes.com/tech/ites",
                "symbol": "INFY",
                "content": "Infosys Topaz platform integrates customized generative AI agent architecture for Tier-1 financial institutions.",
                "sentiment": "BULLISH",
                "sentiment_score": 0.80,
                "published_at": (now - timedelta(hours=8)).isoformat(),
            },
            {
                "title": "Nifty 50 approaches record high propelled by foreign institutional inflows and capital goods rally",
                "source": "CNBC-TV18",
                "url": "https://www.cnbctv18.com/market",
                "symbol": "NIFTY 50",
                "content": "Benchmark Indian indices witnessed broad-based participation with domestic institutional funds matching global risk-on appetite.",
                "sentiment": "BULLISH",
                "sentiment_score": 0.70,
                "published_at": (now - timedelta(hours=10)).isoformat(),
            }
        ]

        if sym:
            filtered = [n for n in market_news if n["symbol"] == sym]
            if not filtered:
                # Generate a symbol-specific simulated article
                filtered.append({
                    "title": f"{sym} demonstrates steady revenue trajectory and margin expansion in sector review",
                    "source": "Market Wire India",
                    "url": "https://www.genstockmarket.local/news",
                    "symbol": sym,
                    "content": f"Quarterly operational analysis for {sym} shows healthy order book momentum and stable balance sheet leverage.",
                    "sentiment": "BULLISH",
                    "sentiment_score": 0.65,
                    "published_at": (now - timedelta(hours=1)).isoformat(),
                })
            return filtered[:limit]

        return market_news[:limit]
