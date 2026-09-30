from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AIChatMessage(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    stream: bool = False


class AIChatResponse(BaseModel):
    conversation_id: str
    reply: str
    tool_calls_executed: List[Dict[str, Any]] = []
    created_at: datetime


class AIStockAnalysisResponse(BaseModel):
    symbol: str
    signal: str  # BUY, SELL, WATCH, NO_TRADE, INSUFFICIENT_DATA
    market_regime: str
    entry_zone: Optional[Dict[str, float]] = None
    stop_loss: Optional[float] = None
    targets: List[float] = []
    risk_reward: Optional[float] = None
    confidence: Optional[float] = None
    technical_analysis: Dict[str, Any] = {}
    fundamental_analysis: Dict[str, Any] = {}
    news_analysis: Dict[str, Any] = {}
    risk_analysis: Dict[str, Any] = {}
    supporting_factors: List[str] = []
    opposing_factors: List[str] = []
    invalidation_conditions: List[str] = []
    data_quality: str = "HIGH"
    data_timestamp: datetime
    warnings: List[str] = []


class AINewspaperArticle(BaseModel):
    section: str
    headline: str
    content: str
    data_points: List[str] = []


class AINewspaperResponse(BaseModel):
    edition: str  # PRE_MARKET, INTRADAY, CLOSING
    generated_at: datetime
    market_headline: str
    articles: List[AINewspaperArticle]
    disclaimer: str = "AI Market Newspaper is an automated data synthesis of authorized market feeds. Not investment advice."
