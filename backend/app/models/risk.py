import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class RiskSettings(Base):
    __tablename__ = "risk_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True, index=True)
    max_order_value = Column(Numeric(20, 2), default=500000.00, nullable=False)
    max_daily_loss = Column(Numeric(20, 2), default=25000.00, nullable=False)
    max_portfolio_exposure_pct = Column(Numeric(5, 2), default=0.25, nullable=False)
    max_symbol_exposure_pct = Column(Numeric(5, 2), default=0.10, nullable=False)
    max_position_value = Column(Numeric(20, 2), default=200000.00, nullable=False)
    max_open_positions = Column(Integer, default=10, nullable=False)
    max_quantity = Column(Integer, default=500, nullable=False)
    max_daily_orders = Column(Integer, default=50, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")


class KillSwitch(Base):
    __tablename__ = "kill_switches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope = Column(String(30), default="PLATFORM", nullable=False, index=True)  # PLATFORM, USER, AI_TRADING
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    is_active = Column(Boolean, default=False, nullable=False)
    reason = Column(String(255), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    check_name = Column(String(50), nullable=False, index=True)
    passed = Column(Boolean, nullable=False)
    severity = Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, BLOCK
    rejection_code = Column(String(50), nullable=True)
    rejection_reason = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User")
