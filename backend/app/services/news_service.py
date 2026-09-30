import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.news import NewsArticle, CorporateAction
from app.models.rag import Document, DocumentChunk

INITIAL_NEWS = [
    {
        "title": "RBI Monetary Policy Committee maintains benchmark repo rate at 6.50%",
        "source": "Economic Times",
        "url": "https://economictimes.indiatimes.com/news/economy/policy",
        "symbol": "BANKNIFTY",
        "content": "The Reserve Bank of India Monetary Policy Committee decided unanimously to keep the policy repo rate unchanged at 6.50%. Governor Shaktikanta Das emphasized that economic resilience remains strong while price stability continues to guide the policy framework.",
        "sentiment": "NEUTRAL",
        "sentiment_score": Decimal("0.20"),
        "published_at": datetime.now(timezone.utc) - timedelta(hours=2)
    },
    {
        "title": "Reliance Industries expands new energy gigafactory operations in Jamnagar",
        "source": "LiveMint",
        "url": "https://www.livemint.com/companies/news",
        "symbol": "RELIANCE",
        "content": "Reliance Industries announced key milestone completions for its fully integrated solar photovoltaic and energy storage manufacturing complex in Jamnagar, Gujarat. Management reaffirmed target commissioning within FY26.",
        "sentiment": "BULLISH",
        "sentiment_score": Decimal("0.85"),
        "published_at": datetime.now(timezone.utc) - timedelta(hours=4)
    },
    {
        "title": "TCS signs $1.2 Billion multi-year enterprise transformation partnership with European insurer",
        "source": "Moneycontrol",
        "url": "https://www.moneycontrol.com/news/business",
        "symbol": "TCS",
        "content": "Tata Consultancy Services secured a mega-deal spanning 8 years to modernize core underwriting systems and cloud infrastructure. Deal TCV reinforces positive guidance for operating margin expansion.",
        "sentiment": "BULLISH",
        "sentiment_score": Decimal("0.90"),
        "published_at": datetime.now(timezone.utc) - timedelta(hours=5)
    },
    {
        "title": "HDFC Bank reports 17% YoY credit growth and stable asset quality in quarterly update",
        "source": "Business Standard",
        "url": "https://www.business-standard.com/finance/banking",
        "symbol": "HDFCBANK",
        "content": "HDFC Bank provisional numbers indicated retail deposits expanded by 18.2% while gross non-performing assets remained steady at 1.24%. Net interest margins showed stability quarter-on-quarter.",
        "sentiment": "BULLISH",
        "sentiment_score": Decimal("0.75"),
        "published_at": datetime.now(timezone.utc) - timedelta(hours=6)
    }
]

INITIAL_ANNOUNCEMENTS = [
    {
        "symbol": "TCS",
        "ex_date": datetime.now(timezone.utc) + timedelta(days=12),
        "action_type": "DIVIDEND",
        "description": "Interim Dividend of Rs 28 per equity share",
        "ratio": "Rs 28 / share"
    },
    {
        "symbol": "RELIANCE",
        "ex_date": datetime.now(timezone.utc) + timedelta(days=25),
        "action_type": "BONUS",
        "description": "Bonus Issue of 1:1 approved by Board of Directors",
        "ratio": "1:1"
    },
    {
        "symbol": "INFY",
        "ex_date": datetime.now(timezone.utc) + timedelta(days=18),
        "action_type": "DIVIDEND",
        "description": "Special Dividend of Rs 10 per share alongside interim distribution",
        "ratio": "Rs 10 / share"
    }
]


class NewsService:
    @staticmethod
    async def seed_initial_news(db: AsyncSession) -> None:
        count_res = await db.execute(select(NewsArticle).limit(1))
        if count_res.scalar_one_or_none():
            return

        for item in INITIAL_NEWS:
            chash = hashlib.sha256(item["content"].encode("utf-8")).hexdigest()
            article = NewsArticle(
                title=item["title"],
                source=item["source"],
                url=item["url"],
                symbol=item["symbol"],
                content=item["content"],
                content_hash=chash,
                sentiment=item["sentiment"],
                sentiment_score=item["sentiment_score"],
                published_at=item["published_at"]
            )
            db.add(article)

        for ca in INITIAL_ANNOUNCEMENTS:
            action = CorporateAction(
                symbol=ca["symbol"],
                ex_date=ca["ex_date"],
                action_type=ca["action_type"],
                description=ca["description"],
                ratio=ca["ratio"]
            )
            db.add(action)

        await db.commit()

    @staticmethod
    async def get_news(db: AsyncSession, symbol: Optional[str] = None, limit: int = 20) -> List[NewsArticle]:
        await NewsService.seed_initial_news(db)
        query = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit)
        if symbol:
            query = query.where(NewsArticle.symbol == symbol.upper())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_corporate_actions(db: AsyncSession, symbol: Optional[str] = None) -> List[CorporateAction]:
        await NewsService.seed_initial_news(db)
        query = select(CorporateAction).order_by(CorporateAction.ex_date.asc())
        if symbol:
            query = query.where(CorporateAction.symbol == symbol.upper())
        result = await db.execute(query)
        return list(result.scalars().all())
