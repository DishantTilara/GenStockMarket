from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.news_service import NewsService
from app.schemas.news import NewsArticleResponse, CorporateActionResponse

router = APIRouter(prefix="/news", tags=["News & Filings"])


@router.get("", response_model=List[NewsArticleResponse])
async def get_news_articles(
    symbol: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    return await NewsService.get_news(db, symbol=symbol, limit=limit)


@router.get("/announcements", response_model=List[CorporateActionResponse])
async def get_corporate_announcements(
    symbol: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    return await NewsService.get_corporate_actions(db, symbol=symbol)
