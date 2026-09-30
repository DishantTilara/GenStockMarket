import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class NewsArticleResponse(BaseModel):
    id: uuid.UUID
    title: str
    source: str
    url: Optional[str]
    published_at: datetime
    symbol: Optional[str]
    content: str
    sentiment: str
    sentiment_score: Decimal

    class Config:
        from_attributes = True


class CorporateActionResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    ex_date: datetime
    record_date: Optional[datetime]
    action_type: str
    description: str
    ratio: Optional[str]

    class Config:
        from_attributes = True
