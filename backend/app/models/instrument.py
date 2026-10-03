import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    exchange = Column(String(20), default="NSE", nullable=False, index=True)
    segment = Column(String(20), default="EQUITY", nullable=False)  # EQUITY, INDEX, FUTURE, OPTION
    isin = Column(String(50), nullable=True, index=True)
    lot_size = Column(Integer, default=1, nullable=False)
    tick_size = Column(Numeric(10, 4), default=0.05, nullable=False)
    sector = Column(String(100), nullable=True, index=True)
    provider_symbol = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    minute_bars = relationship("MinuteBar", back_populates="instrument", cascade="all, delete-orphan")
    daily_bars = relationship("DailyBar", back_populates="instrument", cascade="all, delete-orphan")
