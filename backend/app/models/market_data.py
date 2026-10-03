import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, BigInteger, Numeric, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class MarketTick(Base):
    __tablename__ = "market_ticks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Numeric(20, 4), nullable=False)
    quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class MinuteBar(Base):
    __tablename__ = "minute_bars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    interval_start = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Numeric(20, 4), nullable=False)
    high = Column(Numeric(20, 4), nullable=False)
    low = Column(Numeric(20, 4), nullable=False)
    close = Column(Numeric(20, 4), nullable=False)
    volume = Column(BigInteger, default=0, nullable=False)
    source_timestamp = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_complete = Column(Boolean, default=True, nullable=False)
    quality = Column(String(16), default="HIGH", nullable=False)  # HIGH, MEDIUM, LOW
    source = Column(String(32), default="simulated", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("instrument_id", "interval_start", name="uq_instrument_interval_start"),
        Index("idx_minbars_inst_interval", "instrument_id", "interval_start"),
    )

    instrument = relationship("Instrument", back_populates="minute_bars")


class DailyBar(Base):
    __tablename__ = "daily_bars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    trade_date = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Numeric(20, 4), nullable=False)
    high = Column(Numeric(20, 4), nullable=False)
    low = Column(Numeric(20, 4), nullable=False)
    close = Column(Numeric(20, 4), nullable=False)
    volume = Column(BigInteger, default=0, nullable=False)
    vwap = Column(Numeric(20, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("instrument_id", "trade_date", name="uq_instrument_trade_date"),
        Index("idx_dailybars_inst_date", "instrument_id", "trade_date"),
    )

    instrument = relationship("Instrument", back_populates="daily_bars")


class ProviderHealth(Base):
    __tablename__ = "provider_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name = Column(String(50), nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)
    last_event_at = Column(DateTime(timezone=True), nullable=True)
    last_completed_minute = Column(DateTime(timezone=True), nullable=True)
    ingestion_lag_seconds = Column(Numeric(10, 2), default=0.0, nullable=False)
    symbols_expected = Column(Integer, default=0, nullable=False)
    symbols_received = Column(Integer, default=0, nullable=False)
    missing_minutes = Column(Integer, default=0, nullable=False)
    reconnect_count = Column(Integer, default=0, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class AggregatedCandle(Base):
    __tablename__ = "aggregated_candles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), default="NSE", nullable=False)
    timeframe = Column(String(10), nullable=False, index=True)  # 1m, 5m, 15m, 30m, 1h, 1D
    interval_start = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Numeric(20, 4), nullable=False)
    high = Column(Numeric(20, 4), nullable=False)
    low = Column(Numeric(20, 4), nullable=False)
    close = Column(Numeric(20, 4), nullable=False)
    volume = Column(BigInteger, default=0, nullable=False)
    source = Column(String(32), default="market_provider", nullable=False)
    quality = Column(String(16), default="HIGH", nullable=False)
    is_complete = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "interval_start", name="uq_symbol_timeframe_interval"),
        Index("idx_candles_sym_tf_interval", "symbol", "timeframe", "interval_start"),
    )

