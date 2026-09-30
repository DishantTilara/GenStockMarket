import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class TechnicalIndicatorCache(Base):
    __tablename__ = "technical_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    timeframe = Column(String(10), default="1m", nullable=False)  # 1m, 5m, 15m, 1d
    indicator_name = Column(String(50), nullable=False, index=True)
    values = Column(JSON, nullable=False)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_tech_inst_tf_name", "instrument_id", "timeframe", "indicator_name"),
    )
