import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, Index, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    source = Column(String(100), nullable=False)
    url = Column(String(1000), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    symbol = Column(String(50), nullable=True, index=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    sentiment = Column(String(20), default="NEUTRAL", nullable=False)  # BULLISH, BEARISH, NEUTRAL
    sentiment_score = Column(Numeric(5, 2), default=0.0, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class CorporateAction(Base):
    __tablename__ = "corporate_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(50), nullable=False, index=True)
    ex_date = Column(DateTime(timezone=True), nullable=False, index=True)
    record_date = Column(DateTime(timezone=True), nullable=True)
    action_type = Column(String(50), nullable=False)  # DIVIDEND, SPLIT, BONUS, RIGHTS, BUYBACK
    description = Column(String(500), nullable=False)
    ratio = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
