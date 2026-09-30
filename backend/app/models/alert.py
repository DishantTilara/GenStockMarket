import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    condition_type = Column(String(50), nullable=False)  # PRICE_ABOVE, PRICE_BELOW, RSI_OVERBOUGHT, RSI_OVERSOLD, VOLUME_SPIKE, BREAKOUT
    target_value = Column(Numeric(20, 4), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_triggered = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="alerts")
    events = relationship("AlertEvent", back_populates="alert", cascade="all, delete-orphan")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    triggered_price = Column(Numeric(20, 4), nullable=False)
    message = Column(String(500), nullable=False)
    triggered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    alert = relationship("Alert", back_populates="events")
